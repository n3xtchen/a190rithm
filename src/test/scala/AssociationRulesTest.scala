/*
 * AssociationRulesTest.scala
 * Copyright (C) 2017 n3xtchen <echenwen@gmail.com>
 *
 * Distributed under terms of the GPL-2.0 license.
 */

package nextchen

import org.scalatest.FunSpec
import org.scalatest.matchers.ShouldMatchers

class AssociationRulesTest extends FunSpec with ShouldMatchers {
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
      AssociationRules.apriori(D, miniSup).foreach(println)
    }
  }
}

