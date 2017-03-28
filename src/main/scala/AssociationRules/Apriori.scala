/*
 * Apriori.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen.AssociationRules

object Apriori extends AssociationRulesTraits {
  /*
   * X => Y
   * 支持度 miniSup: 同时包含X,Y的文档数/总文档数
   * 置信度 miniCon ：同时包含X,Y的文档数/含有X的文档数
   */

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
}

