# Retained upstream library boundary

`solrs` is an Apache-2.0 Scala/Java client library, not an end-user search application. The upstream project describes it as an asynchronous, non-blocking JVM client with SolrCloud, routing, retry, and load-balancing support. This checkout's exact commit `bea5ebfb37d5b2efee491830756e7d24d05d3e64` is present in upstream history; the local remote is a fork. Those facts establish source provenance and license evidence, not present-day support.

The immutable snapshot contains 194 files/779,554 bytes across 272 commits and declares `2.4.2-SNAPSHOT`, JDK 8, sbt 1.3.3, Scala 2.12.8/2.13.1, and Solr 7.7.2. It also retains historical publishing plugins/settings and an encrypted Travis deployment-key artifact. Do not decrypt or use that artifact, invoke publishing/site-release tasks, or connect integration tests to a shared Solr service.

Before adoption, a named owner must compare this snapshot with current upstream, choose a supported Scala/JDK/Solr matrix, reproduce compilation/unit/integration tests in a disposable network-isolated environment, inventory dependencies and advisories, replace release credentials, and define update/security-patching cadence. This host has no Java runtime or sbt, so no library build is claimed. The checked-in CI intentionally validates only immutable provenance/quarantine metadata and secrets; it cannot certify the historical library.

Deployment belongs to a separate consuming application with its own entry point, user journey, configuration and secret contract, authentication/authorization/tenant model, tests, monitoring, backup/recovery, and release acceptance. Do not add those controls to this reference merely to make it resemble an app.
