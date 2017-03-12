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

  def compress[A](list: List[A]): List[A] = list match {
    case Nil => Nil
    case head :: sec :: tail if head == sec => compress(head :: compress(tail))
    case head :: tail => head :: compress(tail)
  }

  def cartesianProduct[A](list: List[List[A]])(implicit order: Ordering[A]) = {
    for {
      i <- Range(0, list.length) 
      j <- Range(i+1, list.length)
    } yield compress((list(i) ++ list(j)).sorted.toList)
  }

  def countItemOfKeys[A](docs: List[List[A]])(keys: List[A]) = 
    docs.filter(doc => keys.forall(doc.contains)).length

  def apriori[A](docs: List[List[A]], miniSup: Double)(implicit order: Ordering[A]) = {
      val docCnt = docs.length
      val T1 = docs.flatMap(_.toList).map(t=> (t, 1)).groupBy(_._1)
        .map(r => (r._1, r._2.length*1.0/docCnt))

      var cutKeys = T1.filter(kv => kv._2 >= miniSup).toSeq.map(kv=> List(List(kv._1), kv._2)).toList
      var keys = cutKeys.map(x => x(0).asInstanceOf[List[A]])
      var r = cutKeys
      while (keys.length > 0) {
        keys = cartesianProduct(keys).toList
        cutKeys = compress(keys.map(
          key => List(key, countItemOfKeys(docs.map(_.toList))(key)*1.0/docCnt)
        ).filter(kv => kv(1).asInstanceOf[Double] >= miniSup)).toList
        r = r ++ cutKeys
        keys = compress(cutKeys.map(_(0).asInstanceOf[List[A]]).toList).toList
      }
      r.sortWith(_(1).asInstanceOf[Double] > _(1).asInstanceOf[Double])
  }
}
