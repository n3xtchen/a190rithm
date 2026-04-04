
import os
import random

from a190rithm.nlearning.common import matrix
from a190rithm.nlearning.layers import linear, softmax, rmsnorm
from a190rithm.nlearning.blocks import attention

def gpt(state_dict, token_id, pos_id, n_layer, n_head, head_dim, keys, values):

    tok_emb = state_dict['wte'][token_id] # token embedding
    pos_emb = state_dict['wpe'][pos_id] # position embedding

    x = [t + p for t, p in zip(tok_emb, pos_emb)] # joint token and position embedding
    x = rmsnorm(x) # note: not redundant due to backward pass via the residual connection

    for li in range(n_layer):

        x_residual = x
        x = rmsnorm(x)
        w_q = state_dict[f'layer{li}.attn_wq']
        w_k = state_dict[f'layer{li}.attn_wk']
        w_v = state_dict[f'layer{li}.attn_wv']
        x_attn = attention.multi_head_attention(x, n_head, head_dim, w_q, w_k, w_v, keys[li], values[li])

        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])

        x = [a + b for a, b in zip(x, x_residual)]
        # 2) MLP block
        x_residual = x
        x = rmsnorm(x)
        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])
        x = [xi.relu() for xi in x]
        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])
        x = [a + b for a, b in zip(x, x_residual)]

    logits = linear(x, state_dict['lm_head'])
    return logits

    

if __name__ == "__main__":

    # Let there be a Dataset `docs`: list[str] of documents (e.g. a list of names)
    if not os.path.exists('input.txt'):
        import urllib.request
        names_url = 'https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt'
        urllib.request.urlretrieve(names_url, 'input.txt')
    docs = [line.strip() for line in open('input.txt') if line.strip()]
    random.shuffle(docs)
    print(f"num docs: {len(docs)}")
    
    # Let there be a Tokenizer to translate strings to sequences of integers ("tokens") and back
    uchars = sorted(set(''.join(docs))) # unique characters in the dataset become token ids 0..n-1
    BOS = len(uchars) # token id for a special Beginning of Sequence (BOS) token
    vocab_size = len(uchars) + 1 # total number of unique tokens, +1 is for BOS
    print(f"vocab size: {vocab_size}")

    # Initialize the parameters, to store the knowledge of the model
    n_layer = 1     # depth of the transformer neural network (number of layers)
    n_embd = 16     # width of the network (embedding dimension)
    block_size = 16 # maximum context length of the attention window (note: the longest name is 15 characters)

    n_head = 4      # number of attention heads
    head_dim = n_embd // n_head # derived dimension of each head

    # 权重初始化
    state_dict = {'wte': matrix(vocab_size, n_embd), 'wpe': matrix(block_size, n_embd), 'lm_head': matrix(vocab_size, n_embd)}
    for i in range(n_layer):
        state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)
        state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)
        state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)
        state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)
        state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)
        state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)
    params = [p for mat in state_dict.values() for row in mat for p in row] # flatten params into a single list[Value]
    print(f"num params: {len(params)}")

    # Let there be Adam, the blessed optimizer and its buffers
    learning_rate, beta1, beta2, eps_adam = 0.01, 0.85, 0.99, 1e-8
    m = [0.0] * len(params) # first moment buffer
    v = [0.0] * len(params) # second moment buffer
    
    # Repeat in sequence
    num_steps = 1000 # number of training steps
    for step in range(num_steps):
    
        # Take single document, tokenize it, surround it with BOS special token on both sides
        doc = docs[step % len(docs)]
        tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
        n = min(block_size, len(tokens) - 1)
    
        # Forward the token sequence through the model, building up the computation graph all the way to the loss
        keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
        losses = []
        for pos_id in range(n):
            token_id, target_id = tokens[pos_id], tokens[pos_id + 1]
            logits = gpt(state_dict, token_id, pos_id, n_layer, n_head, head_dim, keys, values)
            probs = softmax(logits)
            loss_t = -probs[target_id].log()
            losses.append(loss_t)
        loss = (1 / n) * sum(losses) # final average loss over the document sequence. May yours be low.
    
        # Backward the loss, calculating the gradients with respect to all model parameters
        loss.backward()
    
        # Adam optimizer update: update the model parameters based on the corresponding gradients
        lr_t = learning_rate * (1 - step / num_steps) # linear learning rate decay
        for i, p in enumerate(params):
            m[i] = beta1 * m[i] + (1 - beta1) * p.grad
            v[i] = beta2 * v[i] + (1 - beta2) * p.grad ** 2
            m_hat = m[i] / (1 - beta1 ** (step + 1))
            v_hat = v[i] / (1 - beta2 ** (step + 1))
            p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)
            p.grad = 0
    
        print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}", end='\r')


    # Inference: may the model babble back to us
    temperature = 0.5 # in (0, 1], control the "creativity" of generated text, low to high
    print("\n--- inference (new, hallucinated names) ---")
    for sample_idx in range(20):
        keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
        token_id = BOS
        sample = []
        for pos_id in range(block_size):
            logits = gpt(state_dict, token_id, pos_id, n_layer, n_head, head_dim, keys, values)
            probs = softmax([l / temperature for l in logits])
            token_id = random.choices(range(vocab_size), weights=[p.data for p in probs])[0]
            if token_id == BOS:
                break
            sample.append(uchars[token_id])
        print(f"sample {sample_idx+1:2d}: {''.join(sample)}")


    

