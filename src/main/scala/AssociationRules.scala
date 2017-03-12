/*
 * Apriori.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen

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

  def apriori[A](docs: Seq[Seq[A]], miniSup: Double)(implicit order: Ordering[A]) = {
      val docCnt = docs.length
      var cutKeys = docs
        .flatMap(doc => compress(doc.sorted)) // 去除item 中重复的值
        .groupBy(t => Seq(t))
        .mapValues(_.length*1.0/docCnt) // 计算支持度
        .filter(_._2 >= miniSup) // 剪枝
        .toSeq
      var r = cutKeys
      var keys = cutKeys.map(_._1)

      while (keys.length > 0) {
        // 组成新值，并排序去重
        keys = compress(cartesianProduct(keys).sortBy(_.toString).toList)
        cutKeys = keys.map(
          key => (key, countItemOfKeys(docs)(key)*1.0/docCnt) // 计算支持度
        ).filter(_._2 >= miniSup) // 剪枝
        r = r ++ cutKeys
        keys = cutKeys.map(_._1)
      }
      r
  }
}
