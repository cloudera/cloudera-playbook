# Extra Notes

Impala Port is hardcoded in hue.j2

need to set the safety valve to 21050 when TLS is not enabled

We haven't fully locked down the cluster as per:
https://docs.cloudera.com/documentation/enterprise/5-16-x/topics/sg_sentry_service_config.html

things like preventing CLI access from users from in the hive / sentry / hue groups isn't done

### Extra Thoughts

Add my superuser group in?