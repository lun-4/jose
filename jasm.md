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

write r6
write r11
```

comentado:
```
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
#write r10
#write r4

#mov r10,"raiz de delta"
#write r10
#write r5

# second part
mov r11,2
mov r7,$(r1)
mul r7,r11

#a * 2
mov r10,"a vezes 2"
write r10
write r7

unm r6,r2

mov r10,"menos b"
write r10
write r6

mov r11,$(r6)
sub r11,r5

# soma com r5(-b + sqrt(delta))
add r6,r5

mov r10,"- b + sqrt(delta)"
write r10
write r6

mov r10,"- b - sqrt(delta)"
write r10
write r11

# divide por r7
div r6,r7
div r11,r7

mov r10,"divide os dois por 2*a"
write r10
write r6
write r11

write r6
write r11
```
