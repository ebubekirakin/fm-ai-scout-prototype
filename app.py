import streamlit as st
import json
import re
import time
import groq

st.set_page_config(
    page_title="Futbol Panorama - AI Scout",
    layout="wide"
)

st.markdown("""
<style>
    .fm-box {
        background-color: #2F3640;
        color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    .border-gk { border-top: 4px solid #f1c40f; } /* Sarı - Kaleci */
    .border-def { border-top: 4px solid #3498db; } /* Mavi - Defans */
    .border-mid { border-top: 4px solid #9b59b6; } /* Mor - Orta Saha */
    .border-att { border-top: 4px solid #e74c3c; } /* Kırmızı - Hücum */
    
    .progress-bg {
        width: 100%;
        background-color: #555555;
        border-radius: 5px;
        height: 20px;
    }
    .progress-bar {
        height: 100%;
        background-color: #2ecc71;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Tanımlamaları
if 'lig' not in st.session_state:
    st.session_state.lig = None
if 'takim' not in st.session_state:
    st.session_state.takim = None
if 'kadro' not in st.session_state:
    st.session_state.kadro = []
if 'havuz' not in st.session_state:
    st.session_state.havuz = []
if 'kimya_skoru' not in st.session_state:
    st.session_state.kimya_skoru = None
if 'scout_raporu' not in st.session_state:
    st.session_state.scout_raporu = None
if 'takim_analizi' not in st.session_state:
    st.session_state.takim_analizi = None

def temizle_json(metin):
    match = re.search(r'\{.*\}', metin, re.DOTALL)
    if match:
        return match.group(0)
    return "{}"

super_lig_verileri = {
    "Beşiktaş": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Be%C5%9Fikta%C5%9F_logo.svg/1200px-Be%C5%9Fikta%C5%9F_logo.svg.png",
        "taktiksel_ruh": "Maaş bütçesini ciddi oranda düşürüp gençleşme operasyonu yapıldı. Yönetimin felsefesi alınan hiçbir oyuncudan zarar etmemek. Sergen Yalçın yönetiminde takım mücadeleci bir oyun oynamaya çalışıyor ancak taraftar sabırsız. Hücum hattında Oh Hyeon-gyu mücadeleci ama bitiriciliği konusunda ciddi sıkıntıları var; acil skorer bir isme ihtiyaç var. Sol bek mevkisinde Rıdvan'ın arkası boş, stoper orijinli Yasin Özcan devşirme oynuyor. Safkan ve ofansif bir sol bek ile takımı sırtlayacak skorer bir sol kanat eksikliği çok net. Kalede Ersin ve kiralık Vasquez tam olarak güven vermiyor.",
        "ilk_11": [
            {"Isim": "Ersin Destanoğlu", "Mevki": "Kaleci", "Guc": 74, "Stil": "Çizgi Kalecisi", "Tip": "Yerli"},
            {"Isim": "Svensson", "Mevki": "Sağ Bek", "Guc": 76, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Paulista", "Mevki": "Stoper", "Guc": 78, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Uduokhai", "Mevki": "Stoper", "Guc": 77, "Stil": "Sert Stoper", "Tip": "Yabancı"},
            {"Isim": "Yasin Özcan", "Mevki": "Sol Bek", "Guc": 72, "Stil": "Devşirme", "Tip": "Yerli"},
            {"Isim": "Al Musrati", "Mevki": "Defansif Orta Saha", "Guc": 79, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Gedson Fernandes", "Mevki": "Merkez Orta Saha", "Guc": 81, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Rafa Silva", "Mevki": "On Numara", "Guc": 82, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Milot Rashica", "Mevki": "Sağ Kanat", "Guc": 77, "Stil": "Çalışkan", "Tip": "Yabancı"},
            {"Isim": "Semih Kılıçsoy", "Mevki": "Sol Kanat", "Guc": 76, "Stil": "İçeri Kat Eden", "Tip": "Yerli"},
            {"Isim": "Oh Hyeon-gyu", "Mevki": "Santrfor", "Guc": 73, "Stil": "Mücadeleci", "Tip": "Yabancı"}
        ]
    },
    "Fenerbahçe": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/thumb/8/86/Fenerbah%C3%A7e_SK.png/1200px-Fenerbah%C3%A7e_SK.png",
        "taktiksel_ruh": "Teknik direktör Tedesco yönetiminde, geçiş oyununa yatkın ve yıldız odaklı bir sistem oynanıyor ancak takımda devasa bir santrfor krizi var. Beklenen leblebici golcü alınmadı; sadece çok genç Sidiki Şerif getirildi. Bu yüzden Talisca veya Kerem Aktürkoğlu gibi isimler Sahte 9 oynamak zorunda kalıyor. Orta saha hattı Fred, N Golo Kante ve Guendouzi ile ligin çok üzerinde. Ancak savunmanın sol stoper bölgesinde net bir eksiklik var. Maaş bütçesi iki katına çıkmış durumda, yapılacak transferlerin nokta atışı olması şart. Avrupa listelerinde yedek kulübesi sayısal olarak yetersiz.",
        "ilk_11": [
            {"Isim": "Livakovic", "Mevki": "Kaleci", "Guc": 81, "Stil": "Çizgi Kalecisi", "Tip": "Yabancı"},
            {"Isim": "Osayi-Samuel", "Mevki": "Sağ Bek", "Guc": 79, "Stil": "Hızlı", "Tip": "Yabancı"},
            {"Isim": "Djiku", "Mevki": "Stoper", "Guc": 80, "Stil": "Çevik", "Tip": "Yabancı"},
            {"Isim": "Oosterwolde", "Mevki": "Stoper", "Guc": 77, "Stil": "Atletik", "Tip": "Yabancı"},
            {"Isim": "Kostic", "Mevki": "Sol Bek", "Guc": 78, "Stil": "Ortacı", "Tip": "Yabancı"},
            {"Isim": "N Golo Kante", "Mevki": "Defansif Orta Saha", "Guc": 84, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Fred", "Mevki": "Merkez Orta Saha", "Guc": 83, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Guendouzi", "Mevki": "Merkez Orta Saha", "Guc": 80, "Stil": "Mücadeleci", "Tip": "Yabancı"},
            {"Isim": "Talisca", "Mevki": "On Numara", "Guc": 85, "Stil": "Gölge Golcü", "Tip": "Yabancı"},
            {"Isim": "Maximin", "Mevki": "Sol Kanat", "Guc": 81, "Stil": "Kanat Forvet", "Tip": "Yabancı"},
            {"Isim": "Kerem Aktürkoğlu", "Mevki": "Sağ Kanat", "Guc": 80, "Stil": "İçeri Eden", "Tip": "Yerli"}
        ]
    },
    "Galatasaray": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Galatasaray_Sports_Club_Logo.png/1200px-Galatasaray_Sports_Club_Logo.png",
        "taktiksel_ruh": "Okan Buruk yönetiminde, önde basan ve oyuncuların farklı mevkilerde oynayabildiği esnek bir sistem uygulanıyor. İleride Icardi ve Osimhen gibi durdurulamaz bir hücum gücü var. Ancak stoper ve 6 numara mevkileri kanayan yara. Nelsson'un gidişiyle stoper rotasyonu çöktü; sağ bek Singo ve 6 numara Lemina stoperde devşirme oynatılıyor. Sağ bek ve kanat rotasyonu inanılmaz derecede şişkin. Acil olarak safkan bir 6 numaraya ve net bir stopere ihtiyaç var.",
        "ilk_11": [
            {"Isim": "Muslera", "Mevki": "Kaleci", "Guc": 80, "Stil": "Lider Kaleci", "Tip": "Yabancı"},
            {"Isim": "Jelert", "Mevki": "Sağ Bek", "Guc": 76, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Singo", "Mevki": "Stoper", "Guc": 78, "Stil": "Devşirme", "Tip": "Yabancı"},
            {"Isim": "Lemina", "Mevki": "Stoper", "Guc": 80, "Stil": "Devşirme", "Tip": "Yabancı"},
            {"Isim": "Jakobs", "Mevki": "Sol Bek", "Guc": 77, "Stil": "Ofansif", "Tip": "Yabancı"},
            {"Isim": "Torreira", "Mevki": "Defansif Orta Saha", "Guc": 82, "Stil": "Süpürücü", "Tip": "Yabancı"},
            {"Isim": "Sara", "Mevki": "Merkez Orta Saha", "Guc": 80, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Barış Alper Yılmaz", "Mevki": "Sağ Kanat", "Guc": 79, "Stil": "Fizikli Kanat", "Tip": "Yerli"},
            {"Isim": "Zaha", "Mevki": "Sol Kanat", "Guc": 81, "Stil": "Skorer", "Tip": "Yabancı"},
            {"Isim": "Mertens", "Mevki": "On Numara", "Guc": 80, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Osimhen", "Mevki": "Santrfor", "Guc": 88, "Stil": "Komple Forvet", "Tip": "Yabancı"}
        ]
    },
    "Kocaelispor": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/thumb/3/36/Kocaelispor_1966.png/1200px-Kocaelispor_1966.png",
        "taktiksel_ruh": "Amatörden dönüp 16 yıl sonra Süper Lig'e çıkan efsanevi camia Selçuk İnan'a emanet. Takım, ateşli Hodri Meydan taraftarının önünde mücadeleci bir oyun arıyor. Mali hata lüksü yok. En büyük silahları 1.93 boyunda Bruno Petkovic. Yapılacak transferin ağır taraftar baskısını kaldırabilecek mental güce sahip olması gerekir.",
        "ilk_11": [
            {"Isim": "Gökhan Değirmenci", "Mevki": "Kaleci", "Guc": 70, "Stil": "Çizgi Kalecisi", "Tip": "Yerli"},
            {"Isim": "Ahmet Oğuz", "Mevki": "Sağ Bek", "Guc": 71, "Stil": "Dengeli", "Tip": "Yerli"},
            {"Isim": "Appindangoye", "Mevki": "Stoper", "Guc": 73, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Osman Çelik", "Mevki": "Stoper", "Guc": 70, "Stil": "Sert Stoper", "Tip": "Yerli"},
            {"Isim": "Muharrem Cinan", "Mevki": "Sol Bek", "Guc": 69, "Stil": "Dengeli", "Tip": "Yerli"},
            {"Isim": "Vukovic", "Mevki": "Defansif Orta Saha", "Guc": 72, "Stil": "Yok Edici", "Tip": "Yabancı"},
            {"Isim": "Pedrinho", "Mevki": "Merkez Orta Saha", "Guc": 74, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Mendes", "Mevki": "Sağ Kanat", "Guc": 73, "Stil": "Çizgiye İnen", "Tip": "Yabancı"},
            {"Isim": "Beridze", "Mevki": "Sol Kanat", "Guc": 71, "Stil": "İçeri Eden", "Tip": "Yabancı"},
            {"Isim": "Caktas", "Mevki": "On Numara", "Guc": 73, "Stil": "Gölge Golcü", "Tip": "Yabancı"},
            {"Isim": "Bruno Petkovic", "Mevki": "Santrfor", "Guc": 77, "Stil": "Hedef Forvet", "Tip": "Yabancı"}
        ]
    },
    "Fatih Karagümrük": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/thumb/d/d7/Fatih_Karag%C3%BCmr%C3%BCk_SK.png/1200px-Fatih_Karag%C3%BCmr%C3%BCk_SK.png",
        "taktiksel_ruh": "Marcel Lička yönetiminde tamamen ofansif, izleyenlere şov vadeden, cesur ve riskli bir 4-2-3-1. Lička savunma yapmayı sevmiyor. Kule forvet Thiago Çukur var. Yapılacak transferin bu çılgın, gollü ve riskli ofansif felsefeye uyması şart; salt savunmacı oyuncular sistemi bozar.",
        "ilk_11": [
            {"Isim": "Sirigu", "Mevki": "Kaleci", "Guc": 73, "Stil": "Tecrübeli", "Tip": "Yabancı"},
            {"Isim": "Veseli", "Mevki": "Sağ Bek", "Guc": 71, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Ceccherini", "Mevki": "Stoper", "Guc": 73, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Koray Günter", "Mevki": "Stoper", "Guc": 72, "Stil": "Pasör", "Tip": "Yerli"},
            {"Isim": "Levent Mercan", "Mevki": "Sol Bek", "Guc": 74, "Stil": "Ofansif Bek", "Tip": "Yerli"},
            {"Isim": "Kourbelis", "Mevki": "Defansif Orta Saha", "Guc": 73, "Stil": "Süpürücü", "Tip": "Yabancı"},
            {"Isim": "Rohden", "Mevki": "Merkez Orta Saha", "Guc": 74, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Emre Mor", "Mevki": "Sağ Kanat", "Guc": 75, "Stil": "Driplingci", "Tip": "Yerli"},
            {"Isim": "Can Keleş", "Mevki": "Sol Kanat", "Guc": 73, "Stil": "Kanat", "Tip": "Yerli"},
            {"Isim": "Eysseric", "Mevki": "On Numara", "Guc": 75, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Thiago Çukur", "Mevki": "Santrfor", "Guc": 71, "Stil": "Kule Forvet", "Tip": "Yerli"}
        ]
    },
    "Gençlerbirliği": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/thumb/8/87/Gen%C3%A7lerbirli%C4%9Fi_SK_logo.png/1200px-Gen%C3%A7lerbirli%C4%9Fi_SK_logo.png",
        "taktiksel_ruh": "Hüseyin Eroğlu yönetiminde, mütevazı bütçelerle ve pragmatik/sonuç odaklı futbolla dönen Başkent ekibi. Hücumda en büyük silah Henry Onyekuru'nun hızı. Kadro derinliği eksik; orta saha ve hücum hattına yaratıcı/skorer çilek transfer bekleniyor.",
        "ilk_11": [
            {"Isim": "Ertuğrul Çetin", "Mevki": "Kaleci", "Guc": 69, "Stil": "Çizgi Kalecisi", "Tip": "Yerli"},
            {"Isim": "Nzaba", "Mevki": "Sağ Bek", "Guc": 68, "Stil": "Atletik Bek", "Tip": "Yabancı"},
            {"Isim": "Zuzek", "Mevki": "Stoper", "Guc": 70, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Yasin Güreler", "Mevki": "Stoper", "Guc": 68, "Stil": "Dengeli", "Tip": "Yerli"},
            {"Isim": "Alperen Babacan", "Mevki": "Sol Bek", "Guc": 69, "Stil": "Dengeli", "Tip": "Yerli"},
            {"Isim": "Etebo", "Mevki": "Defansif Orta Saha", "Guc": 73, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Mikail Okyar", "Mevki": "Merkez Orta Saha", "Guc": 68, "Stil": "Çalışkan", "Tip": "Yerli"},
            {"Isim": "Nadir Çiftçi", "Mevki": "Sağ Kanat", "Guc": 69, "Stil": "Kanat Forvet", "Tip": "Yerli"},
            {"Isim": "Henry Onyekuru", "Mevki": "Sol Kanat", "Guc": 76, "Stil": "Hızlı", "Tip": "Yabancı"},
            {"Isim": "Buğra Çağıran", "Mevki": "On Numara", "Guc": 68, "Stil": "Oyun Kurucu", "Tip": "Yerli"},
            {"Isim": "Yatabare", "Mevki": "Santrfor", "Guc": 72, "Stil": "Fizikli", "Tip": "Yabancı"}
        ]
    },
    "Trabzonspor": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/thumb/a/ab/TrabzonsporAmblemi.png/1200px-TrabzonsporAmblemi.png",
        "taktiksel_ruh": "Şenol Güneş'in geri dönüşüyle iç sahada taraftar ateşini arkasına alan, hücumda geniş kanat organizasyonları ve merkezdeki teknik oyuncularla rakibi boğan inatçı takım.",
        "ilk_11": [
            {"Isim": "Uğurcan Çakır", "Mevki": "Kaleci", "Guc": 81, "Stil": "Lider Kaleci", "Tip": "Yerli"},
            {"Isim": "Pedro Malheiro", "Mevki": "Sağ Bek", "Guc": 75, "Stil": "Çizgiye İnen", "Tip": "Yabancı"},
            {"Isim": "Mendy", "Mevki": "Stoper", "Guc": 78, "Stil": "Fizikli", "Tip": "Yabancı"},
            {"Isim": "Denswil", "Mevki": "Stoper", "Guc": 76, "Stil": "Pasör", "Tip": "Yabancı"},
            {"Isim": "Barisic", "Mevki": "Sol Bek", "Guc": 75, "Stil": "Ortacı", "Tip": "Yabancı"},
            {"Isim": "Lundstram", "Mevki": "Defansif Orta Saha", "Guc": 76, "Stil": "Mücadeleci", "Tip": "Yabancı"},
            {"Isim": "Ozan Tufan", "Mevki": "Merkez Orta Saha", "Guc": 75, "Stil": "İki Yönlü", "Tip": "Yerli"},
            {"Isim": "Cham", "Mevki": "On Numara", "Guc": 77, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Visca", "Mevki": "Sağ Kanat", "Guc": 78, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Trezeguet", "Mevki": "Sol Kanat", "Guc": 79, "Stil": "İçeri Eden", "Tip": "Yabancı"},
            {"Isim": "Banza", "Mevki": "Santrfor", "Guc": 79, "Stil": "Hedef", "Tip": "Yabancı"}
        ]
    }
}

# Avrupa Takımları Verileri
avrupa_takimlari_verileri = {
    "Paris Saint-Germain": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/a/a7/Paris_Saint-Germain_FC_logo.png",
        "taktiksel_ruh": "Luis Enrique yönetiminde sistem odaklı makine. Sabit santrfor kullanmıyorlar; Dembele, Barcola, Kvaratskhelia hareketli sahte 9 oynuyor. Bekler çok önde. En büyük zaafları savunma geçişleri ve kontralar. Sabit bekleyen yavaş pivot santrforlar uymaz.",
        "ilk_11": [
            {"Isim": "Donnarumma", "Mevki": "Kaleci", "Guc": 87, "Stil": "Çizgi Kalecisi", "Tip": "Yabancı"},
            {"Isim": "Hakimi", "Mevki": "Sağ Bek", "Guc": 85, "Stil": "Ofansif Bek", "Tip": "Yabancı"},
            {"Isim": "Marquinhos", "Mevki": "Stoper", "Guc": 86, "Stil": "Pasör", "Tip": "Yabancı"},
            {"Isim": "Pacho", "Mevki": "Stoper", "Guc": 81, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Nuno Mendes", "Mevki": "Sol Bek", "Guc": 84, "Stil": "Hızlı Bek", "Tip": "Yabancı"},
            {"Isim": "Vitinha", "Mevki": "Defansif Orta Saha", "Guc": 85, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Zaire-Emery", "Mevki": "Merkez Orta Saha", "Guc": 83, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Joao Neves", "Mevki": "Merkez Orta Saha", "Guc": 82, "Stil": "Çalışkan", "Tip": "Yabancı"},
            {"Isim": "Dembele", "Mevki": "Sağ Kanat", "Guc": 85, "Stil": "Driplingci", "Tip": "Yabancı"},
            {"Isim": "Kvaratskhelia", "Mevki": "Sol Kanat", "Guc": 86, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Barcola", "Mevki": "Santrfor", "Guc": 83, "Stil": "Sahte 9", "Tip": "Yabancı"}
        ]
    },
    "Barcelona": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/a/a2/FC_Barcelona_logo.svg",
        "taktiksel_ruh": "Hansi Flick yönetiminde Tiki-Taka ile agresif Alman şok presinin birleşimi. Defans çizgisi orta sahada, acımasız OFSAYT taktiği var. Fiziksel dayanıklılığı düşük, 5 saniyelik şok prese uymayan oyuncu barınamaz.",
        "ilk_11": [
            {"Isim": "Ter Stegen", "Mevki": "Kaleci", "Guc": 88, "Stil": "Lider Kaleci", "Tip": "Yabancı"},
            {"Isim": "Kounde", "Mevki": "Sağ Bek", "Guc": 85, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Cubarsi", "Mevki": "Stoper", "Guc": 80, "Stil": "Pasör", "Tip": "Yabancı"},
            {"Isim": "Araujo", "Mevki": "Stoper", "Guc": 87, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Balde", "Mevki": "Sol Bek", "Guc": 83, "Stil": "Hızlı Bek", "Tip": "Yabancı"},
            {"Isim": "Pedri", "Mevki": "Merkez Orta Saha", "Guc": 86, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Gavi", "Mevki": "Merkez Orta Saha", "Guc": 84, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Olmo", "Mevki": "On Numara", "Guc": 85, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Yamal", "Mevki": "Sağ Kanat", "Guc": 83, "Stil": "Driplingci", "Tip": "Yabancı"},
            {"Isim": "Raphinha", "Mevki": "Sol Kanat", "Guc": 85, "Stil": "Çalışkan", "Tip": "Yabancı"},
            {"Isim": "Lewandowski", "Mevki": "Santrfor", "Guc": 89, "Stil": "Hedef", "Tip": "Yabancı"}
        ]
    },
    "Bayern Munich": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg/1200px-FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg.png",
        "taktiksel_ruh": "Kompany yönetiminde rakibi hapseden boğucu pres makinesi. Kimmich saf 6 numara. Kane derine inen hibrit canavar. Taktiksel zekası ve fiziksel pres gücü olmayan adam bu makinede oynayamaz.",
        "ilk_11": [
            {"Isim": "Neuer", "Mevki": "Kaleci", "Guc": 87, "Stil": "Lider Kaleci", "Tip": "Yabancı"},
            {"Isim": "Boey", "Mevki": "Sağ Bek", "Guc": 80, "Stil": "Atletik Bek", "Tip": "Yabancı"},
            {"Isim": "Upamecano", "Mevki": "Stoper", "Guc": 84, "Stil": "Fizikli", "Tip": "Yabancı"},
            {"Isim": "Kim Min-jae", "Mevki": "Stoper", "Guc": 85, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Davies", "Mevki": "Sol Bek", "Guc": 85, "Stil": "Hızlı Bek", "Tip": "Yabancı"},
            {"Isim": "Kimmich", "Mevki": "Defansif Orta Saha", "Guc": 88, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Pavlovic", "Mevki": "Merkez Orta Saha", "Guc": 81, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Musiala", "Mevki": "On Numara", "Guc": 88, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Sane", "Mevki": "Sağ Kanat", "Guc": 84, "Stil": "İçeri Eden", "Tip": "Yabancı"},
            {"Isim": "Coman", "Mevki": "Sol Kanat", "Guc": 83, "Stil": "Kanat", "Tip": "Yabancı"},
            {"Isim": "Kane", "Mevki": "Santrfor", "Guc": 90, "Stil": "Komple Forvet", "Tip": "Yabancı"}
        ]
    },
    "Arsenal": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/b/b4/Arsenal_FC.png",
        "taktiksel_ruh": "Arteta ve Jover yönetiminde duran top makinesi. Kornerler Amerikan futbolu seti gibi. Fiziksel mücadeleden kaçan veya oyun zekası düşük oyuncu sistemi bozar.",
        "ilk_11": [
            {"Isim": "Raya", "Mevki": "Kaleci", "Guc": 85, "Stil": "Çizgi Kalecisi", "Tip": "Yabancı"},
            {"Isim": "White", "Mevki": "Sağ Bek", "Guc": 84, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Saliba", "Mevki": "Stoper", "Guc": 88, "Stil": "Çevik", "Tip": "Yabancı"},
            {"Isim": "Gabriel", "Mevki": "Stoper", "Guc": 87, "Stil": "Fizikli", "Tip": "Yabancı"},
            {"Isim": "Timber", "Mevki": "Sol Bek", "Guc": 82, "Stil": "Ofansif Bek", "Tip": "Yabancı"},
            {"Isim": "Rice", "Mevki": "Defansif Orta Saha", "Guc": 87, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Partey", "Mevki": "Merkez Orta Saha", "Guc": 84, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Odegaard", "Mevki": "On Numara", "Guc": 88, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Saka", "Mevki": "Sağ Kanat", "Guc": 88, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Martinelli", "Mevki": "Sol Kanat", "Guc": 84, "Stil": "Hızlı", "Tip": "Yabancı"},
            {"Isim": "Havertz", "Mevki": "Santrfor", "Guc": 84, "Stil": "Sahte 9", "Tip": "Yabancı"}
        ]
    },
    "Real Madrid": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/1/16/Real_Madrid_logo.png",
        "taktiksel_ruh": "Ancelotti yönetiminde tam bir kaos ve bireysel yıldız parlaması sistemi. Mbappe, Vinicius, Bellingham bir arada çözüm üretiyor. Taktiksel setten çok elit oyuncuların sezgisine bağımlı.",
        "ilk_11": [
            {"Isim": "Courtois", "Mevki": "Kaleci", "Guc": 90, "Stil": "Lider Kaleci", "Tip": "Yabancı"},
            {"Isim": "Carvajal", "Mevki": "Sağ Bek", "Guc": 86, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Rudiger", "Mevki": "Stoper", "Guc": 88, "Stil": "Sert Stoper", "Tip": "Yabancı"},
            {"Isim": "Militao", "Mevki": "Stoper", "Guc": 86, "Stil": "Çevik", "Tip": "Yabancı"},
            {"Isim": "Mendy", "Mevki": "Sol Bek", "Guc": 83, "Stil": "Savunmacı", "Tip": "Yabancı"},
            {"Isim": "Tchouameni", "Mevki": "Defansif Orta Saha", "Guc": 85, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Valverde", "Mevki": "Merkez Orta Saha", "Guc": 89, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Bellingham", "Mevki": "On Numara", "Guc": 90, "Stil": "Gölge Golcü", "Tip": "Yabancı"},
            {"Isim": "Rodrygo", "Mevki": "Sağ Kanat", "Guc": 85, "Stil": "İçeri Eden", "Tip": "Yabancı"},
            {"Isim": "Vinicius Jr", "Mevki": "Sol Kanat", "Guc": 91, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Mbappe", "Mevki": "Santrfor", "Guc": 92, "Stil": "Komple Forvet", "Tip": "Yabancı"}
        ]
    },
    "Liverpool": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/tr/3/3f/150px-Liverpool_FC_logo.png",
        "taktiksel_ruh": "Arne Slot yönetiminde yüksek tempolu ancak aynı zamanda kontrollü pas oyunu oynayan güçlü yapı. Salah ana skor kaynağı, Arnold oyun kurucu bek. Hızlı karar veremeyen oyuncular sırıtıyor.",
        "ilk_11": [
            {"Isim": "Alisson", "Mevki": "Kaleci", "Guc": 89, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Alexander-Arnold", "Mevki": "Sağ Bek", "Guc": 87, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Konate", "Mevki": "Stoper", "Guc": 85, "Stil": "Fizikli", "Tip": "Yabancı"},
            {"Isim": "Van Dijk", "Mevki": "Stoper", "Guc": 89, "Stil": "Lider", "Tip": "Yabancı"},
            {"Isim": "Robertson", "Mevki": "Sol Bek", "Guc": 85, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Gravenberch", "Mevki": "Defansif Orta Saha", "Guc": 83, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Mac Allister", "Mevki": "Merkez Orta Saha", "Guc": 86, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Szoboszlai", "Mevki": "On Numara", "Guc": 84, "Stil": "Şutör", "Tip": "Yabancı"},
            {"Isim": "Salah", "Mevki": "Sağ Kanat", "Guc": 89, "Stil": "Skorer", "Tip": "Yabancı"},
            {"Isim": "Luis Diaz", "Mevki": "Sol Kanat", "Guc": 84, "Stil": "Driplingci", "Tip": "Yabancı"},
            {"Isim": "Jota", "Mevki": "Santrfor", "Guc": 85, "Stil": "Çalışkan", "Tip": "Yabancı"}
        ]
    },
    "Inter": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/1200px-FC_Internazionale_Milano_2021.svg.png",
        "taktiksel_ruh": "Simone Inzaghi'nin kusursuz işleyen 3-5-2 makinesi. Kanat bekleri hücumun asıl gücü, Barella gibi iki yönlü orta sahalar oyunun kalbi. Safkan dördüncü stoper veya statik kanat oyuncularına yer yok.",
        "ilk_11": [
            {"Isim": "Sommer", "Mevki": "Kaleci", "Guc": 85, "Stil": "Çizgi Kalecisi", "Tip": "Yabancı"},
            {"Isim": "Pavard", "Mevki": "Stoper", "Guc": 84, "Stil": "Pasör Stoper", "Tip": "Yabancı"},
            {"Isim": "Acerbi", "Mevki": "Stoper", "Guc": 83, "Stil": "Lider", "Tip": "Yabancı"},
            {"Isim": "Bastoni", "Mevki": "Stoper", "Guc": 87, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Dumfries", "Mevki": "Sağ Kanat", "Guc": 83, "Stil": "Atletik Bek", "Tip": "Yabancı"},
            {"Isim": "Dimarco", "Mevki": "Sol Kanat", "Guc": 86, "Stil": "Ortacı", "Tip": "Yabancı"},
            {"Isim": "Calhanoglu", "Mevki": "Defansif Orta Saha", "Guc": 87, "Stil": "Oyun Kurucu", "Tip": "Yerli"},
            {"Isim": "Barella", "Mevki": "Merkez Orta Saha", "Guc": 88, "Stil": "Dinamolu", "Tip": "Yabancı"},
            {"Isim": "Mkhitaryan", "Mevki": "Merkez Orta Saha", "Guc": 84, "Stil": "Çalışkan", "Tip": "Yabancı"},
            {"Isim": "Thuram", "Mevki": "Santrfor", "Guc": 86, "Stil": "Fizikli", "Tip": "Yabancı"},
            {"Isim": "Martinez", "Mevki": "Santrfor", "Guc": 89, "Stil": "Komple Forvet", "Tip": "Yabancı"}
        ]
    },
    "Borussia Dortmund": {
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Borussia_Dortmund_logo.svg/1200px-Borussia_Dortmund_logo.svg.png",
        "taktiksel_ruh": "Nuri Şahin idaresinde tempolu, hücuma dönük ancak savunma kurgusunda zaman zaman aksayan coşkulu Alman futbolu. Özellikle genç ve potansiyelli hücumculara direkt rol veriliyor.",
        "ilk_11": [
            {"Isim": "Kobel", "Mevki": "Kaleci", "Guc": 87, "Stil": "Çizgi Kalecisi", "Tip": "Yabancı"},
            {"Isim": "Ryerson", "Mevki": "Sağ Bek", "Guc": 80, "Stil": "Çalışkan", "Tip": "Yabancı"},
            {"Isim": "Anton", "Mevki": "Stoper", "Guc": 82, "Stil": "Sert Stoper", "Tip": "Yabancı"},
            {"Isim": "Schlotterbeck", "Mevki": "Stoper", "Guc": 84, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Bensebaini", "Mevki": "Sol Bek", "Guc": 79, "Stil": "Dengeli", "Tip": "Yabancı"},
            {"Isim": "Can", "Mevki": "Defansif Orta Saha", "Guc": 81, "Stil": "Kesici", "Tip": "Yabancı"},
            {"Isim": "Gross", "Mevki": "Merkez Orta Saha", "Guc": 82, "Stil": "Oyun Kurucu", "Tip": "Yabancı"},
            {"Isim": "Brandt", "Mevki": "On Numara", "Guc": 84, "Stil": "Yaratıcı", "Tip": "Yabancı"},
            {"Isim": "Sabitzer", "Mevki": "Sağ Kanat", "Guc": 83, "Stil": "İki Yönlü", "Tip": "Yabancı"},
            {"Isim": "Adeyemi", "Mevki": "Sol Kanat", "Guc": 81, "Stil": "Hızlı", "Tip": "Yabancı"},
            {"Isim": "Guirassy", "Mevki": "Santrfor", "Guc": 84, "Stil": "Hedef Forvet", "Tip": "Yabancı"}
        ]
    }
}

# Başlangıç Transfer Havuzu
baslangic_transfer_havuzu = [
    {"Isim": "Arda Güler", "id": "p1", "Mevki": "On Numara", "Guc": 81, "Stil": "Oyun Kurucu", "Tip": "Yerli"},
    {"Isim": "Ozan Kabak", "id": "p2", "Mevki": "Stoper", "Guc": 77, "Stil": "Kesici", "Tip": "Yerli"},
    {"Isim": "Kerem Aktürkoğlu", "id": "p3", "Mevki": "Sol Kanat", "Guc": 80, "Stil": "İçeri Eden", "Tip": "Yerli"},
    {"Isim": "Salih Özcan", "id": "p4", "Mevki": "Defansif Orta Saha", "Guc": 78, "Stil": "Sert", "Tip": "Yerli"},
    {"Isim": "Kenan Yıldız", "id": "p5", "Mevki": "Santrfor", "Guc": 79, "Stil": "Yaratıcı", "Tip": "Yerli"},
    {"Isim": "Ferdi Kadıoğlu", "id": "p6", "Mevki": "Sol Bek", "Guc": 82, "Stil": "Ofansif Bek", "Tip": "Yerli"},
    {"Isim": "Hakan Çalhanoğlu", "id": "p7", "Mevki": "Merkez Orta Saha", "Guc": 86, "Stil": "Oyun Kurucu", "Tip": "Yerli"},
    {"Isim": "Orkun Kökçü", "id": "p8", "Mevki": "Merkez Orta Saha", "Guc": 80, "Stil": "Şutör", "Tip": "Yerli"},
    {"Isim": "Merih Demiral", "id": "p9", "Mevki": "Stoper", "Guc": 78, "Stil": "Fizikli", "Tip": "Yerli"},
    {"Isim": "İsmail Yüksek", "id": "p10", "Mevki": "Defansif Orta Saha", "Guc": 77, "Stil": "Dinamolu", "Tip": "Yerli"},
    {"Isim": "Yunus Akgün", "id": "p11", "Mevki": "Sağ Kanat", "Guc": 76, "Stil": "Driplingci", "Tip": "Yerli"}
]

# --- SİDEBAR VE VERİ SEÇİMİ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("Groq API Key", type="password")
    
    st.header("🌍 Lig Seçimi")
    lig_secimi = st.radio("Bir Lig Seçin", ["Süper Lig", "Avrupa Devleri"])
    
    if lig_secimi == "Süper Lig":
        aktif_veri = super_lig_verileri
    else:
        aktif_veri = avrupa_takimlari_verileri
        
    takim_isimleri = list(aktif_veri.keys())
    secilen_takim = st.selectbox("Takım Seçin", takim_isimleri)
    
    # Takım değiştiğinde veya ilk açılışta state'i güncelle
    if st.session_state.takim != secilen_takim:
        st.session_state.takim = secilen_takim
        st.session_state.lig = lig_secimi
        # Derin kopya alalım ki orijinal veri bozulmasın
        st.session_state.kadro = [dict((k, v) for k, v in o.items()) for o in aktif_veri[secilen_takim]["ilk_11"] if isinstance(o, dict)]
        st.session_state.havuz = [dict((k, v) for k, v in o.items()) for o in baslangic_transfer_havuzu if isinstance(o, dict)]
            
        # Önceki analizleri temizle
        st.session_state.kimya_skoru = None
        st.session_state.scout_raporu = None
        st.session_state.takim_analizi = None

# --- ANA SAYFA BAŞLIK VE LOGO ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image(aktif_veri[st.session_state.takim]["logo_url"], width=100)
with col_title:
    st.title("Futbol Panorama - AI Scout")
    st.markdown(f"**{st.session_state.takim}** Scout Odası")

# --- TRANSFER ODASI ---
st.markdown("---")
st.subheader("🔄 Transfer Odası (Groq AI)")

if not api_key:
    st.warning("Lütfen sol menüden Groq API Key girin.")
else:
    col_havuz, col_kadro = st.columns(2)
    
    with col_havuz:
        havuz_isimleri = [f"{o['Isim']} ({o['Mevki']} - {o['Guc']})" for o in st.session_state.havuz]
        secilen_havuz_idx = st.selectbox("Havuzdan Girecek Oyuncu", range(len(havuz_isimleri)), format_func=lambda i: havuz_isimleri[i])
        giren_oyuncu = st.session_state.havuz[secilen_havuz_idx]
        
    with col_kadro:
        kadro_isimleri = [f"{o['Isim']} ({o['Mevki']} - {o['Guc']})" for o in st.session_state.kadro]
        secilen_kadro_idx = st.selectbox("Kadrodan Çıkacak Oyuncu", range(len(kadro_isimleri)), format_func=lambda i: kadro_isimleri[i])
        cikan_oyuncu = st.session_state.kadro[secilen_kadro_idx]
        
    if st.button("🚀 Transferi Analiz Et ve Gerçekleştir"):
        with st.spinner("AI Scout Raporu Hazırlanıyor..."):
            try:
                client = groq.Groq(api_key=api_key)
                
                taktiksel_ruh = aktif_veri[st.session_state.takim]["taktiksel_ruh"]
                
                prompt = f"""
                Takım: {st.session_state.takim}. 
                Çıkan: {cikan_oyuncu['Isim']} ({cikan_oyuncu['Mevki']}, {cikan_oyuncu['Stil']}, Güç: {cikan_oyuncu['Guc']})
                Giren: {giren_oyuncu['Isim']} ({giren_oyuncu['Mevki']}, {giren_oyuncu['Stil']}, Güç: {giren_oyuncu['Guc']})
                Takımın Ruhu: {taktiksel_ruh}
                
                Bu transfer hocaya ve takıma ne kadar uyar? Çıkan oyuncunun eksikliği ile giren oyuncunun katkısını kıyasla.
                Sadece şu JSON formatında dön, ekstra metin yazma:
                {{"kimya_skoru": integer (0-100 arası), "analiz": "Kısa bireysel rapor, giren oyuncu için", "takim_analizi": "Detaylı kadro uyumu ve taktiğe etkisi"}}
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sen dünyanın en iyi futbol scoutu ve taktik analistisin. Sadece JSON formatında cevap verirsin."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                
                json_text = temizle_json(response.choices[0].message.content)
                veri = json.loads(json_text)
                
                # State'leri güncelle
                st.session_state.kimya_skoru = veri.get("kimya_skoru", 50)
                st.session_state.scout_raporu = veri.get("analiz", "Rapor alınamadı.")
                st.session_state.takim_analizi = veri.get("takim_analizi", "Analiz alınamadı.")
                
                # --- TRANSFER MANTIĞI ---
                # Giren oyuncunun görsel mevkiisini, çıkanın yerine oturması için eşitle
                yeni_oyuncu = giren_oyuncu.copy()
                yeni_oyuncu["Mevki"] = cikan_oyuncu["Mevki"] 
                
                # Kadroyu güncelle
                st.session_state.kadro[secilen_kadro_idx] = yeni_oyuncu
                
                # Çıkan oyuncuyu havuza ekle, gireni havuzdan sil
                st.session_state.havuz.pop(secilen_havuz_idx)
                st.session_state.havuz.append(cikan_oyuncu)
                
                st.success("Transfer Gerçekleşti ve Analiz Edildi!")
                time.sleep(1) # Rerunn'dan önce kısa bekleme
                st.rerun()
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {str(e)}")

# --- SAHA ÇİZİMİ (4-2-3-1) ---
st.markdown("---")
st.subheader("🏟️ Güncel Kadro (4-2-3-1)")

def oyuncu_karti(oyuncu):
    mevki = oyuncu["Mevki"]
    if "Kaleci" in mevki: border_class = "border-gk"
    elif "Bek" in mevki or "Stoper" in mevki: border_class = "border-def"
    elif "Saha" in mevki or "Numara" in mevki: border_class = "border-mid"
    else: border_class = "border-att"
    
    st.markdown(f"""
    <div class="fm-box {border_class}">
        <div style="font-size: 0.8rem; color: #aaa;">{mevki}</div>
        <div style="font-weight: bold; font-size: 1.1rem; margin: 5px 0;">{oyuncu['Isim']}</div>
        <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
            <span style="color: #f39c12;">⭐ {oyuncu['Guc']}</span>
            <span>{oyuncu['Stil']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Kadrodaki oyuncuları mevkilere göre bulma helper
def bul(aranan_mevki):
    for o in st.session_state.kadro:
        if o["Mevki"] == aranan_mevki:
            return o
    return {"Isim": "Bos", "Mevki": aranan_mevki, "Guc": 0, "Stil": "?"}

# Santrfor (1)
col_st = st.columns([1, 1, 1])
with col_st[1]:
    oyuncu_karti(bul("Santrfor"))

# Ofansif Orta Saha / Kanatlar (3)
col_amc = st.columns(3)
with col_amc[0]: oyuncu_karti(bul("Sol Kanat"))
with col_amc[1]: oyuncu_karti(bul("On Numara"))
with col_amc[2]: oyuncu_karti(bul("Sağ Kanat"))

# Merkez Orta Sahalar (2)
col_mc = st.columns([1, 1, 1, 1])
with col_mc[1]: 
    try: oyuncu_karti(bul("Defansif Orta Saha"))
    except: oyuncu_karti(bul("Merkez Orta Saha")) # 2. bir Merkez OS ise hata vermesin diye
with col_mc[2]: oyuncu_karti(bul("Merkez Orta Saha"))

# Defans (4)
col_def = st.columns(4)
with col_def[0]: oyuncu_karti(bul("Sol Bek"))
# İki stoperi ayırmak için basit mantık
stoperler = [o for o in st.session_state.kadro if o["Mevki"] == "Stoper"]
with col_def[1]: 
    if len(stoperler) > 0: oyuncu_karti(stoperler[0])
with col_def[2]: 
    if len(stoperler) > 1: oyuncu_karti(stoperler[1])
with col_def[3]: oyuncu_karti(bul("Sağ Bek"))

# Kaleci (1)
col_gk = st.columns([1, 1, 1])
with col_gk[1]: oyuncu_karti(bul("Kaleci"))

# --- RAPOR ÇIKTISI ---
if st.session_state.kimya_skoru is not None:
    st.markdown("---")
    st.subheader("📊 Yapay Zeka Scout Raporu")
    
    skor = st.session_state.kimya_skoru
    
    if skor < 40: renk = "#e74c3c" # Kırmızı
    elif skor < 70: renk = "#f1c40f" # Sarı
    else: renk = "#2ecc71" # Yeşil
    
    st.markdown(f"**Takım Kimyası Skoru: {skor}/100**")
    st.markdown(f"""
    <div class="progress-bg">
        <div class="progress-bar" style="width: {skor}%; background-color: {renk};"></div>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    st.success(f"**Bireysel Katkı:** {st.session_state.scout_raporu}")
    st.info(f"**Takım Analizi:** {st.session_state.takim_analizi}")
