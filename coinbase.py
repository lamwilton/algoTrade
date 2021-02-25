import os

import cbpro
import seaborn as sns
import matplotlib.pyplot as plt

public_client = cbpro.PublicClient()

keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/credentials.txt")
keyfile = open(keyfilepath, 'r')
key = keyfile.readline().strip('\n')
b64secret = keyfile.readline().strip('\n')
passphrase = keyfile.readline().strip('\n')

auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase)

test = public_client.get_product_historic_rates('BTC-USD', granularity=3600)
close = []
for item in test:
    close.insert(0, item[4])
sns.set()
plt.plot(close)
plt.show()
print()