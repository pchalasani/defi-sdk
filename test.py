if __name__ == "__main__":
    limit = 11
    for i in range(10):
        try:
            print("try", i)
            if i < limit:
                raise ValueError()
        except:
            print("not larger")
        else:
            print("is larger", i)
            break
    else:
        raise ValueError("FU")
    print("finish")
