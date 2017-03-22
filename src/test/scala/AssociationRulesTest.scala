/*
 * AssociationRulesTest.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen

import org.scalatest.FunSpec
import org.scalatest.Matchers

class AssociationRulesTest extends FunSpec with Matchers {
  describe("关联分析") {
    import AssociationRules._

    val D = List(
      List('A','B','C','D'),
      List('B','C','E'),
      List('A','B','C','E'),
      List('B','D','E'),
      List('A','B','C','D')
    )
    val miniSup = .6

    it("Apriori") {
      Apriori.apriori(D, miniSup).foreach(println)
      Apriori.aprioriRecur(D, miniSup)// .foreach(println)
    }

    it("FP-Tree 构建") {
      val fpGrowth = new FPTree[Char]
      for (item <- Seq(Seq('b', 'a'), Seq('b'))) 
        fpGrowth.add(item)
      println(fpGrowth.children)
    }

    it("FP-Tree 条件模式基") {
      val cpb = Seq(
        Seq(('a', 5.0), ('b', 4.0), ('c', 2.0)),
        Seq(('a', 2.0), ('c', 1.0))
        )
      var cpt = FPGrowth.conditionPatternTree(cpb)

      var dP = cpt.children('a')
      println(dP)
      for (a <- Seq('b')) {
        dP = dP.children(a) 
        println(dP)
      }
      cpt.neighbor.map(x=> x._1 -> x._2.neighborhood.map(_.cnt).sum).foreach(println)
    }

    it("FPGowth 算法过程") {
      FPGrowth.fpGrowth(D, miniSup).foreach(println)
    }
  }
}

