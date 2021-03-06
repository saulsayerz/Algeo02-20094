from PIL import Image, ImageChops
import numpy
import io
import sys
import time
from numpy import random, linalg
# Kalau misal nanti dipakai komentarnya dihapus aja buat baca URL jadi gambar dan sebaliknya
'''import requests 
from io import BytesIO, StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile'''

# BTW INI AKU ASUMSI RASIO (TINGKAT KOMPRESI) ITU PERBANDINGAN SINGULAR_VALUES_DIGUNAKAN / SINGULAR_VALUES_TOTAL YA GAIS
# SOALNYA DI SPEK TUBES TULISANNYA "formatnya dibebaskan, cth: Jumlah singular value yang digunakan"

# KAMUS

# Fungsi SVD menggunakan aproksimasi nilai singular dengan metode power method.
def svd(matriksawal, k):
    # Membuat definisi panggilan
    baris = len(matriksawal)
    kolom = len(matriksawal[0])

    # Menginisialisasi matriks hasil dekomposisi svd
    kiri = numpy.zeros((baris, 1))
    tengah = []
    kanan = numpy.zeros((kolom, 1))

    # Mencari nilai matriks untuk sebanyak k awal yang dibutuhkan
    for i in range(k):
        # Men-transpose matriks awal
        matriksawaltranspos = numpy.transpose(matriksawal)

        # Mencari hasil perkalian dot dari transpos matriks awal dengan matriks awal itu sendiri
        matriksgabungan = numpy.dot(matriksawaltranspos, matriksawal)

        # Mencari nilai x
        x = random.normal(0, 1, size=kolom)
        for j in range(10): # pengulangan sebanyak 10 kali untuk memastikan vektor x yang didapat seakurat mungkin
            x = numpy.dot(matriksgabungan, x)
        
        # Mencari nilai distribusi gauss
        normx = numpy.linalg.norm(x)
        v = numpy.divide(x,normx,where=normx!=0)
        
        # mencari nilai singularnya dan menambahkan ke matriks tengah
        nilaisingular = linalg.norm(numpy.dot(matriksawal, v))
        matriksawalv = numpy.dot(matriksawal, v)
        tengah.append(nilaisingular)

        # Mengisi matriks kiri
        u = numpy.reshape(numpy.divide(matriksawalv,nilaisingular,where=nilaisingular!=0), (baris, 1))
        kiri = numpy.concatenate((kiri,u), axis = 1)

        # Mengisi matriks kanan
        v = numpy.reshape(v, (kolom, 1))
        kanan = numpy.concatenate((kanan,v), axis = 1)

        # Mengurangi matriks awal sebelumnya untuk diproses next valuenya
        matriksawal = matriksawal - numpy.dot(numpy.dot(u, numpy.transpose(v)), nilaisingular)
    
    # Mengembalikan kiri,tengah, dan kanan transpose
    return kiri[:, 1:], tengah, numpy.transpose(kanan[:, 1:])

def banyaknyaKdigunakan(matriksawal,rasio):
    baris, kolom = matriksawal.shape[0], matriksawal.shape[1], 
    if baris < kolom :
        total = baris
    else :
        total = kolom
    digunakan = round((rasio/100)*total)
    return digunakan

# Fungsi ini menconvert gambar ke matriks dengan mengecek modeawal terlebih dahulu.
def gambartomatriks(gambarawal):
    modePA = False # MENGECEK MODE AWALNYA APAKAH P ATAU PA, KARENA HARUS DICONVERT KE RGBA DULU AGAR AMAN
    modeP = False # KALAU MODE AWALNYA RGB,RGBA,L,LA SUDAH AMAN TERPROSES
    if gambarawal.mode == 'P' :
        gambarawal = gambarawal.convert('RGBA')
        modeP = True
    if gambarawal.mode == 'PA':
        gambarawal = gambarawal.convert('RGBA')
        modePA = True
    matriksawal = numpy.array(gambarawal)  # convert gambarnya jadi matriks
    return modeP, modePA, matriksawal

# Fungsi ini mengubah matriks ke gambar, diubah ke unsigned int 0 - 255 dahulu sesuai elemen RGB / L
def matrikstogambar(matrikshasil):
    numpy.clip(matrikshasil,0,255,matrikshasil)
    matriksunsigned = matrikshasil.astype('uint8') 
    hasilgambar = Image.fromarray(matriksunsigned)
    return hasilgambar

# Fungsi ini membuat RGB / L nya 0 apabila transparansinya 0 untuk menghemat memori. Parameter boolean berwarna untuk menentukan jenisnya
def buangpixelsisa(matrikshasil, berwarna) :
    if (berwarna):
        indekstransparansi = 3 #kalau RGBA, A ada di indeks 3. kalau LA, A ada di indeks 1
    else :
        indekstransparansi = 1
    for baris in range(matrikshasil.shape[0]) :
        for kolom in range (matrikshasil.shape[1]):
            if matrikshasil[baris,kolom,indekstransparansi] == 0 : # APABILA TRANSPARANSINYA 0
                matrikshasil[baris,kolom,0] = 0  # MAKA PIXEL GAMBARNYA JUGA DIBUAT 0
                if (berwarna) :
                    matrikshasil[baris,kolom,1] = 0
                    matrikshasil[baris,kolom,2] = 0
    return matrikshasil


# TLDR : ini ngambil matriks dari sebuah gambar, pake SVD, singular values dari matriks nya cuman dipake beberapa bergantung rasio
# Trus matriksnya dikaliin lagi, diconvert balik jadi gambar. Trus ngereturn gambar hasil, banyaknya singular values, singular values digunakan

# INI UNTUK KOMPRESI VERSI GAMBAR RGB UNTUK TIDAK TRANSPARAN, RGBA UNTUK TRANSPARAN
def kompresgambarwarna(matriksawal, rasio,transparan):
    k= banyaknyaKdigunakan(matriksawal,rasio)
    print("banyaknya singularvalues total adalah", k/(rasio/100))
    print("banyaknya singular values digunakan adalah", k)
    if (transparan):
        matrikshasil = numpy.zeros((matriksawal.shape[0], matriksawal.shape[1], 4)) #Inisialisasi matriks kosong sebagai hasilnya
    else :
        matrikshasil = numpy.zeros((matriksawal.shape[0], matriksawal.shape[1], 3))
    for warna in range(3): 
        kiri, tengah, kanan = svd(matriksawal[:,:,warna],k) # ini dekomposisi jadi kiri tengah kanan
        tengah = numpy.diag(tengah) #biar tengahnya jadi matriks, bukan array berisi singular values
        matrikshasil[:,:,warna] = kiri[:, 0:k] @ tengah[0:k,0:k] @ kanan[0:k,:] #mengalikan kembali matriksnya
    if (transparan):
        matrikshasil[:,:,3] = matriksawal[:,:,3]
        matrikshasil = buangpixelsisa(matrikshasil,True)
    hasilgambar = matrikstogambar(matrikshasil)
    return hasilgambar

# Sama seperti kompres gambar, tetapi versi L dan LA
def kompresgambargrey(matriksawal, rasio, transparan):
    k= banyaknyaKdigunakan(matriksawal,rasio)
    print("banyaknya singularvalues total adalah", k/(rasio/100))
    print("banyaknya singular values digunakan adalah", k)
    if (transparan):
        matrikshasil = numpy.zeros((matriksawal.shape[0], matriksawal.shape[1], 2))  #Inisialisasi matriks kosong sebagai hasilnya
        kiri, tengah, kanan = svd(matriksawal[:,:,0],k) 
    else :
        matrikshasil = numpy.zeros((matriksawal.shape[0], matriksawal.shape[1])) 
        kiri, tengah, kanan = svd(matriksawal,k) # ini dekomposisi jadi kiri tengah kanan
    tengah = numpy.diag(tengah) #biar tengahnya jadi matriks, bukan array berisi singular values
    if (transparan) :
        matrikshasil[:,:,0] = kiri[:, 0:k] @ tengah[0:k,0:k] @ kanan[0:k,:] #mengalikan kembali matriksnya kalau transparan
        matrikshasil[:,:,1] = matriksawal[:,:,1]
        matrikshasil = buangpixelsisa(matrikshasil,False)
    else :
        matrikshasil = kiri[:, 0:k] @ tengah[0:k,0:k] @ kanan[0:k,:] #mengalikan kembali matriksnya kalau tidak transparan
    hasilgambar = matrikstogambar(matrikshasil)
    return hasilgambar

def selisihbytes(gambarawal, gambarakhir):
    bytesawal = io.BytesIO()
    gambarawal.save(bytesawal, 'png')
    bytesakhir = io.BytesIO()
    gambarakhir.save(bytesakhir, 'png')
    print("ukuran gambar awal adalah", bytesawal.tell(), "bytes")
    print("ukuran gambar akhir adalah", bytesakhir.tell(), "bytes")
    print("Persentase perubahan pixel adalah", abs(bytesawal.tell() - bytesakhir.tell())*100/bytesawal.tell(), "persen")
    persenselisih = abs(bytesawal.tell() - bytesakhir.tell())*100/bytesawal.tell()
    return persenselisih

def selisihpixel(gambarawal,gambarakhir):
    if gambarawal.mode == 'P' or gambarawal.mode == 'PA':
        gambarakhir = gambarakhir.convert('RGBA')
        gambarawal = gambarawal.convert('RGBA')
    selisih = ImageChops.difference(gambarawal, gambarakhir)
    selisih.show()
    selisihmatrix = numpy.array(selisih)
    if (gambarawal.mode == 'L'):
        persenselisih = selisihmatrix.sum()*100/(selisihmatrix.shape[0]*selisihmatrix.shape[1]*255)
    elif (gambarawal.mode == 'LA' ):
        persenselisih = selisihmatrix[:,:,0].sum()*100/(selisihmatrix.shape[0]*selisihmatrix.shape[1]*255)
    else :
        persenselisih = selisihmatrix[:,:,0:3].sum()*100/(selisihmatrix.shape[0]*selisihmatrix.shape[1]*255*3)
    return persenselisih

    
# ALGORITMA

# print("SELAMAT DATANG DI PROGRAM COMPRESSION K32 SARAP")
gambarawal = Image.open('../../test/jokowi.jpeg')
print("Format gambar awal:", gambarawal.mode)
modeP, modePA, matriksawal = gambartomatriks(gambarawal) # convert gambarnya jadi matriks

rasio = int(input("Silahkan input rasio K yang ingin digunakan: ")) #INPUT RASIO, NANTI DAPET DARI INPUT DI WEBSITE HARUSNYA
waktuawal = time.time()

if (matriksawal.ndim == 3) : 
    if (matriksawal.shape[2] == 3) : # KASUS RGB 
        gambarakhir = kompresgambarwarna(matriksawal, rasio,False) 
    elif (matriksawal.shape[2] == 4) : # KASUS RGBA 
        gambarakhir = kompresgambarwarna(matriksawal, rasio,True) 
    elif (matriksawal.shape[2] == 2) : # KASUS LA
        gambarakhir = kompresgambargrey(matriksawal, rasio, True) 
    if (modeP) :
        gambarakhir = gambarakhir.convert('P') # KASUS P DICONVERT BALIK
    if (modePA) :
        gambarakhir = gambarakhir.convert('PA') # KASUS PA DICONVERT BALIK
elif (matriksawal.ndim == 2) : # KASUS L 
        gambarakhir = kompresgambargrey(matriksawal,rasio, False)

gambarakhir.show()
print("Format gambar akhir:", gambarakhir.mode)

persenselisih = selisihpixel(gambarawal,gambarakhir)
print("Persentase perubahan pixel adalah", persenselisih, "persen")

waktuakhir = time.time()
waktueksekusi = waktuakhir - waktuawal
print("waktu eksekusi program adalah", waktueksekusi)