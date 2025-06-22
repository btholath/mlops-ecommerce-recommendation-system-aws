
import json
import logging

logging.basicConfig(level=logging.INFO)
policy = {
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "kms:Encrypt",
      "kms:Decrypt"
    ],
    "Resource": "*"
  }]
}

logging.info("IAM Policy:
" + json.dumps(policy, indent=2))
