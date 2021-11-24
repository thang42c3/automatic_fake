def check(a):
    # nếu ông thích kiểu if else
    try:

        float(a) # Thằng này đúng
        c = 10/1 # Thằng này lỗi là nó dừng lại luôn, không chạy lặp lại
        print('OK')

    except ValueError:
        print("Not OK")

check(' ')