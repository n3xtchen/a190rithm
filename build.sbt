import AssemblyKeys._
import complete.DefaultParsers._

lazy val commonSettings = Seq(
  version := "1.0.0",
  organization := "com.17173",
  scalaVersion := "2.11.8",
  ivyScala := ivyScala.value map { _.copy(overrideScalaVersion = true) }
)

javacOptions ++= Seq("-source", "1.8", "-target", "1.8", "-Xlint")
scalacOptions ++= Seq("-deprecation", "-feature")

lazy val root = (project in file("."))
  .settings(commonSettings: _*)
  .settings(assemblySettings: _*)
  .settings(name := "user-tag")
  .settings(parallelExecution in Test := false) // 关闭并发测试，避免同时创建 Spark报错 

resolvers += Resolver.sonatypeRepo("public")
resolvers += "Typesafe Releases" at "http://repo.typesafe.com/typesafe/maven-releases/" 
resolvers += Resolver.mavenLocal
resolvers += "Spark Packages Repo" at "http://dl.bintray.com/spark-packages/maven"
resolvers += "Repo at github.com/ankurdave/maven-repo" at "https://raw.githubusercontent.com/ankurdave/maven-repo/master"

// additional libraries
libraryDependencies ++= Seq(
  "com.typesafe" % "config" % "1.2.1",
  "org.scalatest" %% "scalatest" % "2.2.4" % "test",
  "org.json4s" %% "json4s-native" % "3.3.0"
)

mergeStrategy in assembly <<= (mergeStrategy in assembly) {
  (old) => {
    case PathList("META-INF", xs @ _*) => MergeStrategy.discard
    case x => MergeStrategy.first
  }
}

