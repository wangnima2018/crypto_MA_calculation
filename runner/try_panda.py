
import pandas as pd
import matplotlib.pyplot as plt


"""
d = [[1, 2], [3, 4]]

df = pd.DataFrame(d, columns=['col1', 'col2'])
print(df)
"""

data = {'Unemployment_Rate': ['2021-01-19 16:00:00', '2021-01-19 17:00:00', '2021-01-19 18:00:00'],
        'Stock_Index_Price': [1500, 1520, 1525]
        }


df = pd.DataFrame(data, columns=['Unemployment_Rate', 'Stock_Index_Price'])
print(df)

df.plot(x ='Unemployment_Rate', y='Stock_Index_Price', kind = 'line')
plt.show()