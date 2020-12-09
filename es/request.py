'''module to hold the Elastic-Search query objects

Rather than pollute the code with the query information, hide them behind
a variable name.
'''

import datetime
import json

# the dataset will need to change
ALL_ACTIVE_AOI = json.loads('''
{
  "bool": {
    "must": [
      {
        "term": {
          "dataset_type.raw": "area_of_interest"
        }
      },
      {
        "term": {
          "dataset.raw": "aoitrack-earthquake"
        }
      },
      {
        "range": {
          "endtime": {
            "gt": "''' + datetime.datetime.utcnow().isoformat('T','seconds') +
                            '''Z"
          }
        }
      }
    ]
  }
}''')
