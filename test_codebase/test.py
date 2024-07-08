class MyClass:

    def __init__(self, one: str, two: int):
        """
        Init the class. Careful: do not touch!
        """
        self.one = one
        self.two = two

    def do_stuff():
        test = 5 + 3
        if test == 8:
            print(test)
        else:
            print('ups')
        return ''

class MyClass2:

    def another_way_to_do_stuff(self, i: int) -> int:
        return i % 12 + 35