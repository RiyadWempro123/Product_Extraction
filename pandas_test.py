import pandas as pd

s = pd.Series([10, 20, 30,40,50])
# print(s)

data = {
    "name": ["A", "B", "C"],
    "age": [25, 30, 35]
}

df = pd.DataFrame(data, columns=["name", "age"])
# print(df[1:])
myList = [
    ["John", 28],
    ["Sara", 32]
]
df = pd.DataFrame(myList, columns=["name", "age"])
print("iloc",df.iloc[0])
print("loc", df.loc[0])