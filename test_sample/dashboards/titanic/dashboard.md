# Titanic Survival

The training set has 891 labelled passengers. Use the filters to isolate a cohort, then read the charts left to right: survival first splits by sex, then by class, then by age, fare, and travel party.

::: filters
<filter-select name="sex" label="Sex" options="data:train.csv:Sex" default="all" />
<filter-select name="pclass" label="Class" options="all,1,2,3" default="all" />
<filter-select name="embarked" label="Embarked" options="all,C,Q,S" default="all" />
:::

::: grid cols=4
<metric name="passengers" />
<metric name="survival_rate" />
<metric name="survivors" />
<metric name="median_fare" />
:::

::: tabs
::: tab name="Survival"
## Survival Structure

Women survive at a much higher rate than men, and class sharply changes the odds inside each sex. Third-class women are the main exception to the simple "women survived" rule.

::: grid cols=2
<fig name="sex_class_survival" />
<fig name="survival_counts" />
:::
:::

::: tab name="Demographics"
## Demographics

Children have better outcomes than adults, but age alone is weaker than sex and class. Small travel parties do best; solo passengers and large families both fare worse.

::: grid cols=2
<fig name="age_band_survival" />
<fig name="family_survival" />
:::
:::

::: tab name="Fare and port"
## Fare And Embarkation

Fare is a proxy for cabin position and class. Embarkation at Cherbourg also looks favorable, largely because those passengers are richer and more often first class.

::: grid cols=2
<fig name="fare_band_survival" />
<fig name="embarked_class_mix" />
:::
:::
:::

## Rule Of Thumb

A simple transparent rule is close to a basic model: predict survival for females, plus children under 10 in first or second class.

::: grid cols=2
<table name="rule_accuracy" />
<table name="cohort_summary" />
:::

## Rows

<table name="raw_rows" />
