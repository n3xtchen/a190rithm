/*
 * AssociationRulesTraits.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen.AssociationRules

trait AssociationRulesTraits {
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
}

