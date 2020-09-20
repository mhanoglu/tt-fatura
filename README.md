# Türk Telekom Fatura Görüntüleyici

Scripti kullanarak Türk Telekom Online İşlemler sayfasını görüntülemeden telefon numaranız ve tek seferlik şifrenizi kullanarak tüm faturalarınızı listeyelebilirsiniz.

Python-Scrapy kütüphanesi kullanılarak hazırlanmış. Bu nedenle ilk olarak gerekli kurulumları yapmamız gerekiyor. Script Python 2 sürümü ile uyumludur.



## Kurulum

Kullandığım işletim sistemi Ubuntu 18.04. Eğer farklı bir işletim sistem sistemi kullanıyorsanız resmi [Scrapy Installation Documentation]  sayfasından faydalanabilirsiniz. 

Kuruluma başlamadan önce bilgisayarınızda Python yüklü olduğuna emin olunuz.

1. İlk olarak bağımlılıkları yüklüyoruz.

   Python 2 için 

   ```
sudo apt-get install python python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
   ```
   
   Python 3 için 
   
   ```
sudo apt-get install python3 python3-dev python3-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
   ```
   
2. Scrapy kütüphanesini yüklüyoruz

   ```
   sudo pip install scrapy
   ```

3. Yükleme işleminin sonrasında `scrapy` komutu sistem genelinde aktif olacaktır. Aşağıdaki gibi deneyebilirsiniz.

```
mehmet@hanoglu:~$ scrapy
Scrapy 1.8.0 - no active project

Usage:
  scrapy <command> [options] [args]

Available commands:
  bench         Run quick benchmark test
  fetch         Fetch a URL using the Scrapy downloader
  genspider     Generate new spider using pre-defined templates
  runspider     Run a self-contained spider (without creating a project)
  settings      Get settings values
  shell         Interactive scraping console
  startproject  Create new project
  version       Print Scrapy version
  view          Open URL in browser, as seen by Scrapy

  [ more ]      More commands available when run from project directory

Use "scrapy <command> -h" to see more info about a command
```

Projeyi çalıştırabilmek için gerekli kurulumlar bu kadar. 



## Kullanım

1. Projeyi bilgisayarınız indiriniz.

2. Ardından `spiders` dizinine gitmek için aşağıdaki komutu kullanabilirsiniz.

```
cd tt-fatura/scrapyProject/spiders
```

3. Scripti çalıştırma için iki parametreye ihtiyacınız var. 

   `phone` Telefon numaranızı başında 0 olmadan girmelisiniz.

   `code` **9520**'ye **SIFRE** yazarak atacağınız sms'e gelen cevaptaki 6 haneli kodu girmelisiniz.

   Aşağıdaki örnekte 5554443322 telefon numarası ve 123456 kodu ile bir örnek mevcut.

```
scrapy runspider turk-telekom.py -a phone=5554443322 -a code=123456
```

4. Komutu çalıştırdıktan sonra ekranda aşağıdaki gibi bir tablo göreceksiniz.

```
Fatura Tutarı     Fatura Kesim Tarihi        Son Ödeme Tarihi                  Tarife            Ödeme Durumu
           33              23.08.2020              16.09.2020   İnterneti Aşmayan 5GB                  Ödendi
        32.75              23.07.2020              17.08.2020   İnterneti Aşmayan 5GB                  Ödendi
         10.5              23.06.2020              16.07.2020   İnterneti Aşmayan 5GB                  Ödendi
```



## Akış

1. İlk olarak login için istek atıyoruz.

   ```
   curl --location --request POST 'https://onlineislemler.turktelekom.com.tr/oim/sso/login/msisdn' \
   --header 'Content-Type: application/json' \
   --data-raw '{
       "msisdn": "5554443322",
       "otp": "123456",
       "kmli": true
   }'
   ```

   Bu istek sonucunda JSON formatında bir yanıt alıyoruz. `payload.tokenDetails.refreshToken` ve `payload.tokenDetails.accessToken` değerleri mevcut. Bu bilgileri sonraki isteklerde kullanmak üzere saklıyoruz.

	```
	{
        "payload": {
            "tokenDetails": {
                "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUz....",
                "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9......",
                "loginType": "MSISDN"
            },
            "customerState": {
                "msgUnified": false,
                "mgrouped": false,
                "hasMultipleMobileSubscription": false,
                "loginMethod": 1,
                "allDataLineExceptLoggedIn": false
            },
            "previousLogins": [
                {
                    "date": "1600610173926",
                    "state": "SUCCESS"
                }
            ],
            "customerName": "MEHMET HANOĞLU"
        },
        "_code": "200",
        "_message": "Success",
        "_referenceCode": "200",
        "_links": [
            {
                "href": "/oim",
                "rel": "/linkrels/oim"
            },
            {
                "href": "/sso/logout",
                "rel": "/linkrels/sso/logout"
            }
        ]
    }
	```

​		

2. Session bilgisini tutan mysessionid adlı cookie'nin oluşması için aşağıdaki isteği atıyoruz.

   ```
   curl --location --request POST 'https://onlineislemler.turktelekom.com.tr/mps/Portal?cmd=tekilOim' \
   --header 'Referer: https://onlineislemler.turktelekom.com.tr' \
   --header 'Content-Type: application/x-www-form-urlencoded' \
   --header 'Cookie: access_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...' \
   --data-urlencode 'assetId=5383286789'
   ```

   Burada loginde elde ettiğimiz `payload.tokenDetails.accessToken`  bilgisini cookie'ye ekliyoruz. Dönen yanıt bir sayfa olacaktır.

   

3. Bir önceki istekten dönen yanıt aslında otomatik olarak form isteği gönderen ara bir sayfa. Sayfadaki kodları incelersek;

   Javascript koduna göre: Önceki adımda localstorage'e kaydetmiş olduğu `accessToken` ve `refreshToken`  bilgilerini input'lara setliyor.

   ```
   $(document).ready(function() {
   
   	document.getElementById("accessTokenId").value = localStorage.getItem("accessToken");
   	document.getElementById("refreshTokenId").value = localStorage.getItem("refreshToken");
   
   	localStorage.removeItem('selectedMenu');
   	localStorage.removeItem('selectedMenuItem');
   
   	document.checkAuthForm.submit();
   
   	$(".start-overlay").stop(true).show();
   });
   ```

   Yukarıda javascript kodu ile veri setlenen form aşağıdadır. Dikkat etmemiz gereken `assetId` değeri girdiğimiz telefon numarasının başına `90` eklenmiş hali olmasıdır.

    ```
    <form method="POST" id="checkAuthForm" name="checkAuthForm">
        <input name="accessToken" id="accessTokenId" type="hidden">
        <input name="refreshToken" id="refreshTokenId" type="hidden">
        <input value="true" name="fromLegacy" id="fromLegacyId" type="hidden">
        <input name="assetId" id="msisdn" type="hidden" value="905554443322">
        <input name="pageCmd" id="pageCmd" type="hidden">
        <input name="corpUni" id="corpUni" type="hidden" value="">
    </form>
    ```
   
   Bu bilgileri doldurarak tekrar aynı adrese istek atıyoruz.
   
   ```
   curl --location --request POST 'https://onlineislemler.turktelekom.com.tr/mps/Portal?cmd=tekilOim' \
   --header 'Referer: https://onlineislemler.turktelekom.com.tr' \
   --header 'Content-Type: application/x-www-form-urlencoded' \
   --header 'Cookie: access_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...' \
   --data-urlencode 'assetId=5383286789&assetId=905554443322&pageCmd=&corpUni=&fromLegacy=true&refreshToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUz....&accessToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...'
   ```
   
   Bu istekte gönderdiğimiz tüm verileri, ilk isteği atarken de biliyoruz. Bu nedenle 1.adımı atlayarak direkt olarak 2.adımı uygulayabiliriz.



4. Ardından fatular sayfası için istek atıyoruz. Attığımız istek sonrasında elde ettiğimiz html dokümanı parse ederek fatura bilgilerimize erişiyoruz.

   Her bir fatura bilgisi aşağıdaki gibi `table > tr` içindeki `td` elementlerinde tutulmaktadır. Parse işlemi sonrasın tüm bilgileri yalın bir halde alıyoruz.
   

	```
    <tr bgcolor="#fdfdfd">
        <td>
            <div class="radio-container pull-left">
                <i class="radio-fake-icon glyphicon glyphicon-unchecked"></i><input id="selectedBill" name="selectedBill" type="radio" value="23.07.2020;20201122424444;32.75;; YES;ME****HA****;20200817; YES;" data-cutoff="23.07.2020" data-billid="20201122424444" data-amount="32.75" data-period="202007" data-billtype="" data-subscription="YES" data-name="ME****HA****" data-duedate="20200817" data-status="YES">
            </div>32.75
        </td>
        <td>23.07.2020</td>
        <td>17.08.2020</td>
        <td>İnterneti Aşmayan 5GB</td>
        <td>
            <form target="popupInvoiceInfo" id="frmInvoiceInfo" method="post" name="frmInvoiceInfo" ....</form>
        </td>
        <td>
            <strong>
                <p>&Ouml;dendi<span class="bill-image-paid"></span></p>
            </strong>
        </td>
    </tr>
	```


[Scrapy Installation Documentation]: https://docs.scrapy.org/en/latest/intro/install.html

