import cs50
import sys

def main():
    if len(sys.argv) == 1:
        print("Enter a numerical key")
        return 1
        
    else:
        k = int(sys.argv[1])
        
        print("Enter a string")
        s = cs50.get_string()
        
        for i in s:
            if i.isalpha():
                if i.isupper():
                    new_i = ((ord(i) - 65) + k) % 26 + 65
                    j = chr(new_i)
                    print(j, end="")
                    
                elif i.islower():
                    new_i = ((ord(i) - 97) + k) % 26 + 97
                    j = chr(new_i)
                    print(j, end="")
            
            else:
                print(i)
               
        print()
        return 0

if __name__ == "__main__":
    main()
