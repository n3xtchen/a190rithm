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

    val D = List(
      List('A','B','C','D'),
      List('B','C','E'),
      List('A','B','C','E'),
      List('B','D','E'),
      List('A','B','C','D')
    )
    val miniSup = .6

    it("Apriori") {
      // AssociationRules.apriori(D, miniSup).foreach(println)
      // AssociationRules.aprioriRecur(D, miniSup).foreach(println)
    }

    it("FP-Growth") {
      val fpGrowth = FPGrowth(' ')
      for (item <- D) 
        fpGrowth.add(item)
      println(fpGrowth.tree.children('A'))
    }
  }
}

