# IDPRO BODY OF KNOWLEDGE USAGE REPORTING

## Acquiring usage data

The geographic usage data is sourced from https://bok.idpro.org/manager/plugins/reporting/geo .

A monthly data series is created by exporting the report as a comman separated values file.

The file is encoded as UTF-8 and is stored in the data folder with the prefix `bok_geo_use_` and the suffix of the month as `yyyymm`.

For example `bok_geo_use_202211`.

Some countries, such as `Côte d'Ivoire`, require unicode support.

## Notes for automation

A screen scraper is implemented to gather the data from Janeway.  It is located in `janeway.py`.

Credentials are stored in `private/config.yaml` which is not stored in git.  They two keys are `user_name` and `user_pass`.

As of now its pulling a hardcoded list of months.  A mechanism to pull only missing items or most recent should be designed.

## Generating graphics

The `country_chart` program generates a chart for all the time periods for which data files exist.  It is named with the start and end month as as follows:

`bok_usage_chart_202004_to_202301.html`

