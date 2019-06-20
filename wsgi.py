import numpy as np

truc='13G7M32QAM_ISM6XMC5D_X'
pouet='RTN380AX_80G_62.5M_256QAM'



if truc.split('_').__len__()<4:
    div = truc.split('_')
    #div2= pouet.split('_')
    mod = div[0].split('G')
    #mod2 = div2[0].split('G')
    print('freq = '+mod[0]+' Bandwidth : '+mod[1].split('M')[0])
    #print('freq = '+mod2[0]+' Bandwidth : '+mod2[1].split('M')[0])

#RTN380AX_80G_62.5M_256QAM


requip = truc.split('_')
print(requip)