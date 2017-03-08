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

  def apriori[A](docs: List[List[A]], miniSup: Double) {
    var r = List.empty
    val docCnt = docs.length
    val T1 = docs.flatMap(_.toList).map(t=> (t, 1)).groupBy(_._1).map(r => (r._1, r._2.length*1.0/docCnt))

    // r = T1.filter(_._2 >= miniSup)
    
    println(T1)
    
  }
}

