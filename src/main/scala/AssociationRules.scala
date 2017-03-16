/*
 * Apriori.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen

// 树节点
class FPNode[A](val name: A, val parent: Option[FPNode[A]]=None, val neighbor: Option[FPNode[A]]=None) {

  var cnt: Int = 1
  var children = scala.collection.mutable.Map[A, FPNode[A]]()

  def increment() {
    cnt = cnt + 1
  }

  def getChild(name: A) = children.get(name)

  def addChild(node: FPNode[A]) = getChild(node.name) match {
    case Some(_: FPNode[A]) => throw new Exception("重复添加节点")
    case None => {
      children(node.name) = node
    }
  }

  override def toString() = s"FPNODE(name:$name,cnt:$cnt)"
}

object FPNode {

  // root 节点声明
  // def apply[A]() = new FPNode(' ')
  def apply[A](root: A) = new FPNode(root)

  // 节点
  def apply[A](name: A, parent: FPNode[A], neighbor: Option[FPNode[A]]) = new FPNode(name, Some(parent), neighbor)
}

class FPGrowth[A](val tree: FPNode[A]) {
  var neighbor = scala.collection.mutable.Map[A, FPNode[A]]()

  def add(transaction: List[A]) {
    var node = tree
    for (name <- transaction) {
      node = node.getChild(name) match {
        case Some(n: FPNode[A]) => {
          n.increment()
          n
        }
        case None => {
          val s_neighbor = neighbor.get(name)
          val newNode = FPNode(name, node, s_neighbor)
          neighbor(name) = newNode
          node.addChild(newNode)
          newNode
        }
      }
    }
  } 

  def neighborhood(node: FPNode[A]): Seq[FPNode[A]] = node.neighbor match {
    case Some(n) => {
      Seq(node) ++ neighborhood(n)
    }
    case None => Seq(node)
  }

  /*
   * 条件模式基
   */
  def conditionPatternBase(node: FPNode[A], minSup: Double, cnt: Int, subffix: Seq[A]=Nil): Seq[(Seq[A], Int)] = node.parent match {
    case Some(n) => {
      val sub = node.name +: subffix
      Seq((sub, cnt)) ++ conditionPatternBase(n, minSup, cnt, sub)
    }
    case None => Nil
  }

  def run() {
    val minSup = 2
    for ((k, v) <- neighbor) {
      for (x <- neighborhood(v)) {
        conditionPatternBase(x, minSup, x.cnt).filter(_._2 > minSup).foreach(println)
      }
    }
  }
}

object FPGrowth {
  def apply[A](root: A) = {
    new FPGrowth(FPNode(root))
  }
}

object AssociationRules {
  /*
   * X => Y
   * 支持度 miniSup: 同时包含X,Y的文档数/总文档数
   * 置信度 miniCon ：同时包含X,Y的文档数/含有X的文档数
   */

  // 去重连续重复
  def compress[A](list: Seq[A]): Seq[A] = list match {
    case Nil => Nil
    case head :: sec :: tail if head == sec => compress(head +: compress(tail))
    case head :: tail => head +: compress(tail)
  }

  // 生成集合
  def cartesianProduct[A](list: Seq[Seq[A]])(implicit order: Ordering[A]) = {
    for {
      i <- Range(0, list.length) 
      j <- Range(i+1, list.length)
    } yield compress((list(i) ++ list(j)).sorted)
  }

  // 计算包含该键的项数
  def countItemOfKeys[A](docs: Seq[Seq[A]])(keys: Seq[A]) = 
    docs.filter(doc => keys.forall(doc.contains)).length

  // 计算每一项的文档频数
  def freqK1[A](docs: Seq[Seq[A]])(implicit order: Ordering[A]) = docs
    .flatMap(doc => compress(doc.sorted)) // 去除item 中重复的值
    .groupBy(t => Seq(t))
    .mapValues(_.length*1.0) // 计算支持度
    .toSeq

  def apriori[A](docs: Seq[Seq[A]], miniSup: Double)(implicit order: Ordering[A]) = {
    val docCnt = docs.length
    var cutKeys = freqK1(docs).filter(_._2/docCnt >= miniSup) // 剪枝

    var r: Seq[(Seq[A], Double)] = Nil
    do {
      r = r ++ cutKeys
      cutKeys = compress(cartesianProduct(cutKeys.map(_._1)).sortBy(_.toString).toList) // 组成新值，并排序去重
        .map(key => (key, countItemOfKeys(docs)(key)*1.0)) // 计算支持度
        .filter(_._2/docCnt >= miniSup) // 剪枝
    } while (cutKeys.length > 0)
    r
  }

  def aprioriRecur[A](docs: Seq[Seq[A]], miniSup: Double)(implicit order: Ordering[A]) = {
      val docCnt = docs.length
      // k = 1
      var cutKeys = freqK1(docs).filter(_._2/docCnt >= miniSup) // 剪枝
      // k > 1
      def recur(keys: Seq[(Seq[A], Double)]): Seq[(Seq[A], Double)] = keys match {
        case Nil => Nil
        case _: Seq[(Seq[A], Double)] => {
          // 组成新值，并排序去重
          val newKeys = compress(cartesianProduct(keys.map(_._1)).sortBy(_.toString).toList)
            .map(
              key => (key, countItemOfKeys(docs)(key)*1.0) // 计算支持度
            ).filter(_._2/docCnt >= miniSup) // 剪枝
          newKeys ++ recur(newKeys)
        }
      }
      cutKeys ++ recur(cutKeys)
  }

  def fpGrowth[A](docs: Seq[Seq[A]], miniSup: Double)(implicit order: Ordering[A]) = {
      val docCnt = docs.length
      // k = 1
      var cutKeys = freqK1(docs).filter(_._2/docCnt >= miniSup) // 剪枝
      // 生成头表
      val headTable = cutKeys.sortBy(-_._2)

      // 基于头表排和去除剪枝
      val keyOrder = headTable.map(_._1(0))
      val newDocs = docs.map(doc => {
        for {
          k <- keyOrder
          if doc.contains(k)
        } yield k
      }.toList)

      val fpTree = FPGrowth(' '.asInstanceOf[A])
      for (doc <- newDocs) {
        fpTree.add(doc)
      }

      // newDocs.foreach(println)

      headTable.foreach(println)
      fpTree.run()
  }
}
