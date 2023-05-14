# Definition Lists

This file demonstrates the use of definition lists.

<!-- [[[
    DefinitionList(
        {
            "coffee": "Hot drink.",
            "milk": "Cold drink.",
            "water": "Hot or cold drink.",
            "Gatorade": DefinitionListType.DefinitionInfo(
                "Drink marketed to athletes (https://www.gatorade.com/).",
                postprocess_type=DefinitionListType.PostprocessType.Exact,
            ),
        },
    )
]]] -->
<p>
  <div><i><a id="coffee">coffee</a></i></div>
  <div>&nbsp;&nbsp;Hot drink.</div>
</p>
<p>
  <div><i><a id="milk">milk</a></i></div>
  <div>&nbsp;&nbsp;Cold drink.</div>
</p>
<p>
  <div><i><a id="water">water</a></i></div>
  <div>&nbsp;&nbsp;Hot or cold drink.</div>
</p>
<p>
  <div><i><a id="gatorade">Gatorade</a></i></div>
  <div>&nbsp;&nbsp;Drink marketed to athletes (https://www.gatorade.com/).</div>
</p>
<!-- [[[end]]] -->

## Samples

### Standard
- I drink <a href="#coffee" data-definition-list-link=1>coffee</a> in the morning.
- I have <a href="#milk" data-definition-list-link=1>milk</a> with my cereal.
- <a href="#water" data-definition-list-link=1>Water</a> is good any time of the day.
- I drink <a href="#gatorade" data-definition-list-link=1>Gatorade</a> when I play sports, but that doesn't happen too often anymore.

### Case Sensitivity

- <a href="#coffee" data-definition-list-link=1>Coffee</a>, <a href="#coffee" data-definition-list-link=1>coffee</a>
- <a href="#milk" data-definition-list-link=1>Milk</a>, <a href="#milk" data-definition-list-link=1>milk</a>
- <a href="#water" data-definition-list-link=1>Water</a>, <a href="#water" data-definition-list-link=1>water</a>
- <a href="#gatorade" data-definition-list-link=1>Gatorade</a>, gatorade (the latter will not be matched because `postprocess_type` is set to `DefinitionList.PostprocessType.Exact`)

### Stemming

- <a href="#coffee" data-definition-list-link=1>Coffee</a>
- <a href="#milk" data-definition-list-link=1>Milk</a>, <a href="#milk" data-definition-list-link=1>milks</a>, <a href="#milk" data-definition-list-link=1>milked</a>, <a href="#milk" data-definition-list-link=1>milking</a>
- <a href="#water" data-definition-list-link=1>Water</a>, <a href="#water" data-definition-list-link=1>waters</a>, <a href="#water" data-definition-list-link=1>watered</a>, <a href="#water" data-definition-list-link=1>watering</a>
- <a href="#gatorade" data-definition-list-link=1>Gatorade</a>, Gatorades (only the exact match will be decorated because `postprocess_type` is set to `DefinitionList.PostprocessType.Exact`)
