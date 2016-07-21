joseassembly tests:


bhaskara:

```assembly
mov r1,2
mov r2,-14
mov r3,12

mov r4,$(r2)
mov r5,2
pow r4,r5
mov r5,4
mov r6,$(r1)
mov r7,$(r3)
mul r5,r6
mul r5,r7
sub r4,r5
mov r5,$(r4)
sqrt r5

mov r11,2
mov r7,$(r1)
mul r7,r11
unm r6,r2
mov r11,$(r6)
sub r11,r5
add r6,r5
div r6,r7
div r11,r7

echo r6
echo r11
```

comentado:
```assembly
mov r1,2
mov r2,-14
mov r3,12

# b ao quadrado
mov r4,$(r2)
mov r5,2
pow r4,r5

mov r5,4
mov r6,$(r1)
mov r7,$(r3)
mul r5,r6
mul r5,r7

sub r4,r5

mov r5,$(r4)
sqrt r5

#mov r10,"delta"
#echo r10
#echo r4

#mov r10,"raiz de delta"
#echo r10
#echo r5

# second part
mov r11,2
mov r7,$(r1)
mul r7,r11

#a * 2
mov r10,"a vezes 2"
echo r10
echo r7

unm r6,r2

mov r10,"menos b"
echo r10
echo r6

mov r11,$(r6)
sub r11,r5

# soma com r5(-b + sqrt(delta))
add r6,r5

mov r10,"- b + sqrt(delta)"
echo r10
echo r6

mov r10,"- b - sqrt(delta)"
echo r10
echo r11

# divide por r7
div r6,r7
div r11,r7

mov r10,"divide os dois por 2*a"
echo r10
echo r6
echo r11

echo r6
echo r11
```

Equality:
```assembly
mov r1,1
mov r2,1
cmp r1,r2
mov r10,"equal"
else
mov r10,"not equal"
cmpe
echo r10
```
