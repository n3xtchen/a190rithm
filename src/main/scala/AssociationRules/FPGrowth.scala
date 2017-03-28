/*
 * FPGrowth.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen.AssociationRules

sealed trait FPTreeTrait[A] {

  var children = scala.collection.mutable.Map[A, FPNode[A]]()
  def getChild(name: A) = children.get(name)

  def addChild(node: FPNode[A]) = getChild(node.name) match {
    case Some(_: FPNode[A]) => throw new Exception("重复添加节点")
    case None => {
      children(node.name) = node
    }
  }
}

// 树节点
class FPNode[A](val name: A, val parent: Option[FPNode[A]]=None, val neighbor: Option[FPNode[A]]=None) extends FPTreeTrait[A] {

  var cnt: Double = 1

  /*
   * 向后（右）寻找相邻的节点
   *
   */
  def neighborhood: Seq[FPNode[A]] = Seq(this) ++ (neighbor match {
    case Some(n) => {
      n.neighborhood
    }
    case None => Nil
  })

  override def toString() = s"FPNODE(name:$name,cnt:$cnt)"
}

object FPNode {

  // 节点
  def apply[A](name: A, parent: FPNode[A], neighbor: Option[FPNode[A]]) = new FPNode(name, Some(parent), neighbor)

  // 最接近根节点
  def apply[A](name: A, neighbor: Option[FPNode[A]]) = new FPNode(name, None, neighbor)
}

class FPTree[A] extends FPTreeTrait[A] {

  var neighbor = scala.collection.mutable.Map[A, FPNode[A]]()

  def getChildOrCreate(name: A, cnt: Double=0) = getChild(name) match {
    case Some(n: FPNode[A]) => {
      n.cnt = n.cnt + (if (cnt > 0) cnt else 1)
      n
    }
    case None => {
      val s_neighbor = neighbor.get(name)
      val newNode = FPNode(name, s_neighbor)
      if (cnt > 0) { newNode.cnt = cnt }
      neighbor(name) = newNode
      addChild(newNode)
      newNode
    }
  }

  /*
   * 初始化FPTree时，使用
   *
   */
  def add(transaction: Seq[A]) = addWithCnt(transaction.map((_, 1.0)))

  /*
   * 构建条件模式树时，使用
   *
   */
  def addWithCnt(transaction: Seq[(A, Double)]) {
    val head :: tail = transaction
    var node = getChildOrCreate(head._1, head._2)
    for ((name, cnt) <- tail) { //去除后缀的节点
      node = node.getChild(name) match {
        case Some(n: FPNode[A]) => {
          n.cnt = n.cnt + cnt
          n
        }
        case None => {
          val s_neighbor = neighbor.get(name)
          val newNode = FPNode(name, node, s_neighbor)
          newNode.cnt = cnt
          neighbor(name) = newNode
          node.addChild(newNode)
          newNode
        }
      }
    }
  }
}

object FPGrowth extends AssociationRulesTraits {
  /*
   * 条件模式基: 向（上）前（Root）匹配路径
   */
  def conditionPatternBase[A](node: FPNode[A]) = {
    val lastCnt = node.cnt
    def recurParent(node: Option[FPNode[A]]): Seq[(A, Double)] = node match {
      case Some(n) => {
        val cnt = if (n.cnt >= lastCnt) lastCnt else n.cnt
        recurParent(n.parent) ++ Seq((n.name, cnt))
      }
      case None => Nil
    }
    recurParent(node.parent)
  }

  /*
   * 条件模式树
   */
  def conditionPatternTree[A](cpb: Seq[Seq[(A, Double)]]) = {
    val fpTree = new FPTree[A]
    for (transction <- cpb) {
      fpTree.addWithCnt(transction)
    }
    fpTree
  }

  def findWithFilter[A](tree: FPTree[A], minSup: Double, postModel: Seq[A]=Nil): Seq[Any] = {
    for ((k, v) <- tree.neighbor) yield {
      val neighborhood_n = v.neighborhood
      val support = neighborhood_n.map(_.cnt).sum
      if (support >= minSup) {
        val newPostModel = k +: postModel
        val cpb = neighborhood_n.map(conditionPatternBase).filter(_.length > 0)
        val cpt = conditionPatternTree(cpb)
        (newPostModel, support) +: findWithFilter(cpt, minSup, newPostModel)
      } else Nil
    }
  }.toSeq.flatten

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

      val fpTree = new FPTree[A]
      for (doc <- newDocs) {
        fpTree.add(doc)
      }

      // 开始迭代
      findWithFilter(fpTree, miniSup*docCnt)
  }
}

