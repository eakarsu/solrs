# Security

This snapshot has no current support or vulnerability-response commitment. Its JDK 8/sbt 1.3.3/Solr 7.7.2 build definition, HTTP Restlet resolver, publishing plugins, old dependency graph, test Solr distribution, and encrypted Travis deployment-key artifact require explicit review; an intact encrypted key is still release material and must never be decrypted or reused.

Do not publish artifacts, invoke release/site tasks, use the legacy key, or connect tests to a shared Solr cluster. Any approved build must run in a disposable least-privilege environment with no production credentials or reachable shared service, strict resource limits, recorded dependency resolution, and cleanup. Preserve `LICENSE.txt`, notices, the exact snapshot evidence, and upstream attribution.

Report suspected issues to the future accountable owner and upstream project as appropriate. A consuming application owns endpoint authentication/TLS, request authorization, tenant isolation, input limits, logging, retry budgets, circuit breaking, data classification, and incident response; none is supplied by this archive boundary.
