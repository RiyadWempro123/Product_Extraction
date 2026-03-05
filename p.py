# class BankAccount:
#     def __init__(self, balance):
#         self.__balance = balance   # private variable

#     def deposit(self, amount):
#         self.__balance += amount

#     def get_balance(self):
#         return self.__balance

# acc = BankAccount(1000)
# acc.deposit(500)
# print(acc.get_balance())

class Person:
    def speak(self):
        print("I can speak....")

class Teacher(Person):
    def teach(self):
        print("I can teach ....")

t = Teacher()
t.speak()
t.teach()
