#!/usr/bin/env python3
"""
inject_dialect_v2.py — Updates dialect songs.json with Chinese + romanization paired lyrics.

Format stored in songs.json:
    Chinese line
    romanization line
    (blank line between sections)

Run: python inject_dialect_v2.py
     python inject_dialect_v2.py --dry-run   (preview without writing)
"""
import json, re, sys, pathlib

SONGS_PATH = pathlib.Path(__file__).parent / "data" / "songs.json"
DRY_RUN = "--dry-run" in sys.argv

KEY_MARKER  = re.compile(r'[A-Ga-gbf#\-/]+ key\s*\|', re.IGNORECASE)
CHORD_RE    = re.compile(
    r'^[\s]*([A-G][#b]?(maj|min|m|sus|add|dim|aug|M)?[0-9]*([/][A-G][#b]?)?[\s]*)+$'
)
CHINESE     = re.compile(r'[一-鿿]')
SECTION_MAP = [
    (re.compile(r'^verse\s*\d*$',       re.I), '[诗段]'),
    (re.compile(r'^chorus\s*\d*$',      re.I), '[副歌]'),
    (re.compile(r'^bridge\s*\d*$',      re.I), '[桥段]'),
    (re.compile(r'^pre.?chorus\s*\d*$', re.I), '[前副歌]'),
    (re.compile(r'^loop\s*\d*$',        re.I), '[循环]'),
    (re.compile(r'^coda\s*\d*$',        re.I), '[结尾]'),
    (re.compile(r'^tag\s*\d*$',         re.I), '[结尾]'),
    (re.compile(r'^intro\s*\d*$',       re.I), '[前奏]'),
    (re.compile(r'^refrain\s*\d*$',     re.I), '[副歌]'),
    (re.compile(r'^interlude\s*\d*$',   re.I), '[间奏]'),
]

# ── Dialect header detection ─────────────────────────────────────────────────

DIALECT_HDR = re.compile(r'[（(]\s*(福|广)\s*[)）]')

def _is_chord(line: str) -> bool:
    s = line.strip().replace('\\#', '#').replace('\\b', 'b')
    return bool(s) and bool(CHORD_RE.match(s))

def _section_label(line: str):
    for pat, label in SECTION_MAP:
        if pat.match(line.strip()):
            return label
    return None

def _is_romanization(line: str) -> bool:
    """True if line has no Chinese characters and looks like romanization (has letters)."""
    s = line.strip()
    return bool(s) and not CHINESE.search(s) and bool(re.search(r'[a-zA-Z]', s))


# ── Main extractor ───────────────────────────────────────────────────────────

def extract_with_romanization(raw: str) -> str:
    """
    Parse raw docx text and return lyrics with Chinese + romanization paired.
    Handles Hokkien (福) and Cantonese (广), single or dual dialect docs.
    """
    lines = raw.split('\n')

    # Find key-version marker positions to isolate first version content
    kp = [i for i, l in enumerate(lines) if KEY_MARKER.search(l)]
    if not kp:
        content = lines
    elif len(kp) == 1:
        content = lines[kp[0]+1:]
    else:
        end = kp[1]
        while end > 0 and not lines[end-1].strip():
            end -= 1
        while end > 0 and lines[end-1].strip():
            end -= 1
        while end > 0 and not lines[end-1].strip():
            end -= 1
        content = lines[kp[0]+1 : end]

    # Detect dialect sections
    dialect_headers = [DIALECT_HDR.search(l).group(1) for l in lines if DIALECT_HDR.search(l)]
    has_both = len(set(dialect_headers)) == 2

    result = []
    current_dialect = None
    i = 0

    while i < len(content):
        line = content[i]
        s = line.strip().replace('\\~', '~').replace('\\#', '#')

        # Dialect section header
        dm = DIALECT_HDR.search(s)
        if dm:
            new_d = dm.group(1)
            if new_d != current_dialect:
                current_dialect = new_d
                if has_both:
                    if result:
                        result.append('')
                        result.append('')
                    result.append('【福建话】' if current_dialect == '福' else '【广东话】')
                    result.append('')
            i += 1
            continue

        # Skip key/bpm lines
        if KEY_MARKER.search(s):
            i += 1
            continue

        # Skip chord-only lines
        if _is_chord(s):
            i += 1
            continue

        # Skip empty
        if not s:
            i += 1
            continue

        # Skip attribution lines
        if s.startswith(('词曲', '作词', '作曲')):
            i += 1
            continue

        # Section labels
        label = _section_label(s)
        if label:
            if result:
                result.append('')
            result.append(label)
            i += 1
            continue

        # Chinese line — look ahead for romanization on next non-empty line
        if CHINESE.search(s):
            result.append(s)
            # peek at next lines for romanization
            j = i + 1
            while j < len(content) and not content[j].strip():
                j += 1
            if j < len(content):
                next_s = content[j].strip().replace('\\~', '~').replace('\\#', '#')
                if _is_romanization(next_s) and not _is_chord(next_s):
                    result.append(next_s)
                    i = j + 1
                    continue
            i += 1
            continue

        # Romanization line not yet consumed (orphan — skip)
        i += 1

    text = '\n'.join(result)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip leaked version-title lines at end (contain 广/福 markers)
    lines_out = text.split('\n')
    while lines_out and DIALECT_HDR.search(lines_out[-1]):
        lines_out.pop()

    return '\n'.join(lines_out).strip()


def norm(title: str) -> str:
    t = re.sub(r'\s*[（(][^)）]*[）)]\s*', '', title)
    return t.strip()


# ── Raw source content ───────────────────────────────────────────────────────
# Each key is the song title (without dialect marker). Value is raw docx text
# with Chinese lines followed immediately by romanization lines.

RAW: dict[str, str] = {}

RAW['我们的上帝是全能的神'] = r"""我们的上帝是全能的神 (广)

D key | 140bpm | 4/4

Verse

D D

我们的上帝是全能的神

ngo mun dik Soeng Dai si qun nang dik San

D A

祂是全能的主

Taa si qun nang dik Ju

A A

我们的上帝是全能的神

ngo mun dik Soeng Dai si qun nang dik San

D

祂是全能的主

Taa si qun nang dik Ju

Chorus

D D

我们要高声来唱哈利路亚

ngo mun yiu gou seng lai coeng ha lei lu ya

G

赞美主圣名

zaan mei Ju seng meng

G D

我们的上帝是全能的神

ngo mun dik Soeng Dai si qun nang dik San

A D

祂是全能的主

Taa si qun nang dik Ju


我们的上帝是全能的神 (福)

D key | 140bpm | 4/4"""

RAW['在耶稣里我们是一家人'] = r"""夸胜 (D)

在耶稣里我们是一家人 (广)

E key | 150bpm 4/4

Verse

E

在耶稣里我们是一家人

zoi Ye-Sou loi ngo mun si yat gaa yan

B7 E E7

在耶稣里我们是一家人

zoi Ye-Sou loi ngo mun si yat gaa yan

Chorus

A

在耶稣里我们是一家人

zoi Ye-Sou loi ngo mun si yat gaa yan

E C\#m

从今至到永永远远

cung gam zi dou wing wing yun yun

F\#m B7 E

在耶稣里 我们是一家人

zoi Ye-Sou loi ngo mun si yat gaa yan

在耶稣里我们是一家人 (广)

F key | 150bpm 4/4"""

RAW['耶稣的名真是美丽'] = r"""耶稣的名真是美丽 (广)

A key | 130bpm | 4/4

Verse

A

耶稣的名真是美丽

Ye-Sou dik meng zan si mei lai

D E

永远在我的心

wing yun zoi ngo dik sam

A F\#m

我要时常爱我的主耶稣

ngo yiu si soeng oi ngo dik Ju Ye-Sou

Bm E A

只要我活着

zi yiu ngo wut zoek

Chorus

A D A

荣耀荣耀 荣耀哈利路亚

wing yiu wing yiu wing yiu ha-lei-lu-ya

A E

颂赞主的圣名

zung zaan Ju dik sing meng

A

耶稣的名真是美丽

Ye-Sou dik meng zan si mei lai

Bm E A

永远在我的心

wing yun zoi ngo dik sam


耶稣的名真是美丽 (福)

A key | 130bpm | 4/4"""

RAW['神对我真好'] = r"""神对我真好 (广)

D key | 140bpm | 4/4

Verse 1

D A D

对我真好 对我真好

doi ngo zan hou do ingo zan hou

D G A D

浩大主爱 我心中感到

hou dai Ju oi ngo sam zung gam dou

Verse 2

神真美好 神真美好

San zan mei hou San zan mei hou

神真美好 祂对我真好

San zan mei hou Taa doi ngo zan hou

Verse 3

祂看顾我 祂看顾我

Taa hon gu ngo Taa hon gu ngo

祂看顾我 每一日看顾

Taa hon gu ngo mui yat ye hon gu

Verse 4

我顺服祂 我顺服祂

ngo seon fook Taa ngo seon fook Taa

我顺服祂 每一日顺服

ngo seon fook Taa mui yat ye seon fook

Verse 5

祂真爱我 祂真爱我

Taa zan oi ngo Taa zan oi ngo

祂真爱我 祂真是爱我

Taa zan oi ngo Taa zan si oi ngo


神对我真好 (福)

D key | 140bpm | 4/4"""

RAW['生命在于祢'] = r"""生命在於祢 G Em

主是 (福)

C key | 68bpm | 4/4

Verse

C G C

主是我生命的力量

Chu si goa si mia e lat liong

F G

是我患难中的高台

si goa hoan lan tiong e ko tai

F G/B C G/B Am

主的爱高深 无法测 度

Chu e ai ko chim bo huat che to

Dm G C

祂是我心的安慰

Yi si goa sim e an ui

Chorus

F G C

祂的爱充满我心

Yi e ai chiong moa goa sim

F G Am

祂恩惠长存

Yi e un hui tiong chun

F G C G/B Am

祂是我生命中力 量

Yi si goa si mia tiong lat liong

Dm G C

是我生命的盼望

si goa si mia e pang bong


主是 (广)

C key | 68bpm | 4/4"""

RAW['赞美耶和华'] = r"""生命在於祢 G Em

赞美耶和华 (福)

赞美之泉

D key | 68bpm | 4/4

Verse

D Bm

我赞美耶和华 我称颂耶和华

goa oh lo Ya-Ho-Hua goa cing siong Ya-Ho -Hua

G A D

我高举双手宣扬

goa go gu siang qiu suan yong

D Bm

我赞美耶和华 我称颂耶和华

goa oh lo Ya-Ho-Hua goa cing siong Ya-Ho -Hua

G A D

我诚心敬拜永不息

goa seng sim geng bai eng bo sua

Chorus

Bm F\#m

万君的君 万王的王

ban Kun eh Kun ban Ong e Ong

G A D

我俯落在祢宝座前

goa gui lo ti Li po zo jeng

Bm F\#m

昔在今在 永远的主

sit zai kim zai eng guan e Chu

G A D

独独祢配得尊崇和荣耀

tok tok Li pui tek zun cong ka eng yao


赞美耶和华 (福)

赞美之泉

C key | 68bpm | 4/4"""

RAW['我要永远跟着耶稣'] = r"""夸胜 (D)

我要永远跟着耶稣 (福)

D key | 140bpm | 4/4

Verse

无论那个风有几大

bo lun li e hong wu lua dua

无论那个雨下几多

bo lun li e ho lo lua zui

我要永远跟着耶稣 向前走

goa beh eng wan dui tiao Ya-So hiong cheng gia

无论世界怎样来说

bo lun se kai an zua lai gong

无论世界怎样来看

bo lun se kai an zua lai kua

我要永远跟着耶稣 向前走

goa beh eng wan dui tiao Ya-So hiong cheng gia

Chorus

我要永远跟着耶稣

goa beh eng wan dui tiao Ya-So

远跟着耶稣

eng wan dui tiao Ya-So

B7 E

永远跟着耶稣 向前走

eng wan dui tiao Ya-So hiong cheng gia


我要永远跟着耶稣 (福)

F key | 140bpm | 4/4"""

RAW['我要歌颂祢圣名'] = r"""Shekinah 荣耀 (G)

我要歌颂祢圣名 (福)

D key | 72bpm | 4/4

Verse 1

D G A

我要歌颂祢圣名 哦主

goa beh go siong Li seng mia oh Chu

F\#m Bm

歌颂祢圣名 哦主

go siong Li seng mia oh Chu

G A D (D7)

因为祢圣名 至高配得赞美

yin wei Li seng mia ji ko pui tek oh lo

Verse 2

D G A

我要荣耀祢圣名 哦主

goa beh eng yao Li seng mia oh Chu

F\#m Bm

荣耀祢圣名 哦主

eng yao Li seng mia oh Chu

G A D (D7)

因为祢圣名 至高配得赞美

yin wei Li seng mia ji ko pui tek oh lo


我要歌颂祢圣名

G key | 72bpm | 4/4"""

RAW['荣耀都归祢'] = r"""荣耀都归祢 (广)

赞美之泉

A key | 72bpm | 4/4

Verse

A E/G\# F\#m7 A/E D A/C\# Bm7 E

哈 利 路亚 荣耀归宝座羔羊

ha lei lu ya wing yiu gwai bou zo gou yoeng

A E/G\# F\#m7 A/E

哈 利 路亚

ha lei lu ya

D A/C\# Bm7 E A

荣耀都归祢 荣耀都归祢真神

wing yiu dou gwai Nei wing yiu dou gwai Nei zan san

Chorus

A E/G\# F\#m7 A/E

我一生都要来敬拜祢

ngo yat saang dou yiu loi ging bai Nei

D A/C\# Bm7 E

哈 利 路 亚

ha lei lu ya

A E/G\# F\#m7 A/E

我的手我的口 我全心我全人

ngo dik sau ngo dik hao ngo qun sam ngo qun yan

Bm7 E A

都要敬拜祢

dou yiu ging bai Nei


荣耀都归祢 (广)

赞美之泉

C key | 72bpm | 4/4"""

RAW['阮吟诗赞美祢'] = r"""阮吟诗赞美祢 (福)

Bm key | 68bpm | 4/4

Verse 1

Bm F\#m

天父上帝请祢来听

Ti-Peh Siong-Tei chia Li lai thia

G A D

阮要吟诗来赞美祢的名

gun beh gim si lai oh lo Li e mia

Em Bm G (A) F\# (Bm)

祢的教训阮要行 祢的话语阮要听

Li e ka si gun beh gia Li e wue gu gun beh thia

Verse 2

主啊祢的疼爱阮嘛知影

Chu a Li e thia tang gun ma zai yia

阮的脚步 求主啊来带领

gun e kha po kiu Chu ah lai toa nia

这条道路 虽然歹行

chi tiau to lo sui lian phai gia

但有主同在 阮嘛唔惊

dan wu Chu tang zai gun ma mm kia

Chorus

主啊 主啊我爱祢 愿阮一生献给祢

Chu ah Chu ah goa ai Li guan gun yit seng hean ho Li

用阮的歌声称颂赞美祢

eng gun e koa sia cheng siong oh oh Li

主啊 主啊我爱祢 愿阮一生见证祢

Chu ah Chu ah goa ai Li guan gun yit seng kian cheng Li

愿一切荣耀拢归祢

guan yit chiat eng yao long kui ho Li

阮吟诗赞美祢 (福)

Bm key | 68bpm | 4/4"""

RAW['祢的恩典每天够我用'] = r"""祢的恩典每天够我用

D key | 70bpm | 4/4

Verse

D F\#m G

祢的恩典每天够我用

Nei dik yan din mui tin gau ngo yung

D Bm Em A

纵有困难也不会逃避

zung yau kwan naan yaa bat wui tou bei

G G/A F\#m Bm

有祢与我一起 我还惧怕什么

yau Nei yu ngo yat hei ngo waan geoi paa sam mo

Em E/G\# A

赐我勇气 去改变自己

ci ngo yung hei heoi goi bin zi gei

Chorus

D F\#m G

啊~啊~耶稣 耶稣 耶稣

ah ah Ye-Sou Ye-Sou Ye-Sou

G E7 A

奉献一生 皆因最爱是祢

fung hin yat sang gaai yan zoi oi si Nei

D Bm G Gm

为了祢我愿将一切抛弃

wai liu Nei ngo yun zoeng yat cai paau hei

Em A D

耶稣 为要得着祢

Ye-Sou wai yiu dak zoek Nei


祢的恩典每天够我用

C key | 70bpm | 4/4"""

RAW['谁曾应许'] = r"""谁曾应许 (广)

C key | 70bpm | 4/4

Verse 1

C E7 Am7

谁曾应许 一生不撇下我

soi cang ying hoi yat sang bat pit haa ngo

Dm7 D7 Gsus G

每段窄路 谁陪我去走过

mui dyun zaak lou soi pui ngo hoi zau gwo

C E7 Am D7

谁还领我于青草恬静处躺卧

soi wan ling ngo yu cing cou tim zing co tong ngo

Dm7 D7 G

丰足恩惠 比海沙更多

fong zuk yan wai bei hoi saa gang do

Verse 2

谁曾应许 天天看顾着我

soi cang ying hoi tin tin hon gu zoek ngo

昼夜眷佑 连头发也数过

zau ye gun yao lin tau faat yaa sou gwo

谁还以爱驱走心里惧怕怯懦

soi wan yi oi koi zau sam loi goi paa hip no

那惧路途卷动着漩涡

naa goi lou tou gyun dung zoek xun wo

Chorus

C Em

因为祢是我主 我避难所

yan Nei si ngo Ju ngo bei naan so

F C/E

我盾牌和诗歌

ngo teon paai wo si go

Dm C/E D7 G

祢是我的高台 我随时帮助

Nei si ngo gou toi ngo soi si bong zo

C G/B

来吧 用信心 赞颂和高歌

loi ba yung seon sam zaan sung wo gou go

Am7 Gm C7

祢永在我心窝

Nei wing zoi ngo sam wo

F C/E

唯祢有永生江河

wai Nei yao wing saang gong ho

Dm7 G C

除祢以外 不倚靠别个

coi Nei yi ngoi bat yi kaau bit go

Coda

F C/E Dm7 G C

我究竟算什么 神祢竟这般顾念我

ngo gau ging syun sam mo San Nei ging ze bun gu nim ngo


谁曾应许 (广)

C key | 70bpm | 4/4"""

RAW['只想亲近祢'] = r"""只想亲近祢 (广)

A key | 72bpm | 4/4

Verse

D A F\#m

只想亲近祢 每天亲近祢

zi seong can gan Nei mui tin can gan Nei

D E A

在恩典里深深遇见祢

zoi yan din lui sam sam yu gin Nei

D A F\#m

只想亲近祢 每刻亲近祢

zi seong can gan Nei mui hak can gan Nei

Bm E A

在恩典里深深认识祢

zoi yan din lui sam sam ying sik Nei

Chorus

Dmaj7 E C\#m7 F\#m

祢是我的依傍 祢是我的高台

Nei si ngo dik yi bong Nei si ngo dik gou toi

Bm E A A7

祢是我藏身处 我的避难所

Nei si~ ngo cong san qu ngo dik bei naan so

Dmaj7 E C\#m7

祢是我的希望 祢是我一生最爱

Nei si ngo dik hei mong Nei si ngo yat sang zeoi oi

F\# B E A

谁人可以像祢 这样无止境爱我

seoi yan ho yi zeong Nei ze yeong mou zi ging oi ngo

Tag

B E A

竟这样无止境爱我

ging ze yeong mou zi ging oi ngo


只想亲近祢 (广）

G key | 72bpm | 4/4"""

RAW['家家青松'] = r"""家家青松 (广)

D key | 130bpm | 4/4

Verse

D

家家青松满室光明

ga ga cing cung mun sat gwong ming

Em D A D

啦啦啦啦啦 啦啦啦啦

la la la la la la la la la

D

因主降临圣歌高咏

yan Ju gong lam sing go gou wing

Em D A D

啦啦啦啦啦 啦啦啦啦

la la la la la la la la la

A D

请跟我来颂赞衷诚

cing gan ngo loi zung zan cung seng

D E A E A

啦啦啦 啦啦啦 啦啦啦

la la la la la la la la la

D

宝贵应许永生吉庆

bou gwai ying hoi wing sang gat heng

G D A D

啦啦啦啦啦 啦啦啦啦

la la la la la la la la la


家家青松 (广)

D key | 130bpm | 4/4"""

RAW['主啊我要跟随祢'] = r"""主啊 我要跟随祢 (福)

G key | 68bpm | 4/4

Verse

G D/F\# Em7 G/D

祢的话掂我心 当我无盼望的时

Li e wueh diam goa sim teng goa bo ng bang e si

C D

导我走过人生的路

choah goa khia khue lin seng e lo

G D/F\# Em7 G/D

祢的疼掂我心 当我无依靠的时

Li e thia diam goa sim teng goa bo oa kho e si

C D

给我盼望走下去

ho goa ng bang khia lohk khi

Chorus

G D/F\# Em7 Bm7

主啊 我要跟随祢 将我一生献给祢

Chu ah goa beh gun tueh Li chiong goa yi seng hean ho Li

C Em7

回应祢的呼召和爱疼

huey ing Li e ho tiao ka thia thang

Am7 D

坚持一生不偏离

khin ci yi seng bo pehn li

G D/F\# Em7 Bm7

主啊 我要跟随祢 将我一生献给祢

Chu ah goa beh gun tueh Li chiong goa yi seng hean ho Li

C Em7

求祢用我做祢的器具

kiu Li eng goa choe Li e khi gu

Am7 D G

将祢的疼分享出去

chiong Li e thia hun hiong chut khi"""

RAW['欢欣'] = r"""欢欣 (广)

D key | 68bpm | 4/4

Verse

D A

欢欣 心里感谢神

foon yan sam loi gam ze San

Bm F\#m

歌唱 归于圣父

go coeng gwai yu sing fu

G D C A

赞颂 祢赐下慈爱独生的爱子

zan zung Nei ci haa ci oi duk sang dik oi zi

Chorus

F\#m Bm Em

今天 心中刚强无惧怕

gam tin sam zung gong koeng mou geoi paa

A D

主的丰盛满一生

Ju dik fung sing mun yat sang

Bm C A

皆因主手曾为我显深恩

gaa yan Ju sau cang wai ngo hin sam yan

D

感恩

gam yan"""

RAW['今我已经得胜了'] = r"""今我已经得胜了 (福)

D key | 140bpm | 4/4

Verse

今我已经得胜了

kim goa yi gin tek seng liao

今我已经得胜了

kim goa yi gin tek seng liao

靠着耶稣所留宝血

kho tioh Ya So sou lao po hoeh

今我已经得胜

kim goa yi gin tek seng

Chorus

耶稣十架

Ya So chap gei

得胜为我

tek seng ui goa

靠着耶稣所留宝血

kho tioh Ya So sou lao po hoeh

我已得胜

goa yi tek seng


今我已经得胜了 (福)

D key | 140bpm | 4/4"""

RAW['亚伯拉罕的上帝'] = r"""亚伯拉罕的上帝 (广)

Am key | 140bpm | 4/4

Verse

Am

亚伯拉罕的上帝 以撒的神

aa-baak-laai-hon dik Soeng Dai ji saat dik San

G Em Dm Am

雅各的上帝是我的神

nga gok dik Soeng Dai si ngo dik San

Am

伟大的上帝 全能真神

wai dai dik Soeng Dai qun nang dik Zan San

G Em Dm Am

伟大的上帝是我的神

wai dai dik Soeng Dai si ngo dik San

Chorus

Am

哈利路亚 哈利路

ha-lei-lu-ya ha-lei-lu

G Am (E Am)

哈利路亚 哈 利 路

ha-lei-lu-ya ha-lei-lu


亚伯拉罕的上帝 (广)

Am key | 140bpm | 4/4"""

RAW['平安的七月夜'] = r"""平安的七月夜 (福)

F key | 70bpm | 4/4

Verse 1

F

夜星在天上闪闪烁

mi chi ti thi teng siam siam si

Dm C

月娘光光照溪边

goeh niu kng kng chio kay pi

Bb F Dm

大树下 风微微 听到树蝉在吟诗

toa chhiu e hong bi bi thia tioh chiu sian teh gim si

Bb C

上帝赏赐的平安夜

Siong-te siu su e peng an mi

Verse 2

耶和华是我的安慰

Ya-ho-hoa si goa e an ui

依靠祂拢免惊什么

oa kho Yi long bian kia sia mih

虽遇到风台天 祂给我心有平静

sui tu tioh hong thai thi Yi ho goa sim u peng cheng

将平安放在我的内心

chiong peng an khng ti goa e lai sim

Chorus

F Dm

我过死荫山谷 也无惊灾害

goa koe si im soa kok ya bo khia chai hai

Bb C

祂会与我伫地 用话来安慰我

Yi e kah goa ti teh eng oe lai an ui goa

F Dm

有恩典和慈爱同我相作伴

u un tian kah chu ai kah goa sa choe phoa

Bb C F

有平安随我一世人

u peng an tueh goa chit si lang


平安的七月夜 (福)

D key | 70bpm | 4/4"""

RAW['同心聚集'] = r"""同心聚集 (广)

D key | 140bpm | 4/4

Verse

D A D G D

同心聚集且一起高声唱

tung sam zeoi zap ce yat hei gou seng coeng

C A D D7

愿彼此谦卑一起崇拜祂

yun bei ci him bei yat hei sung baai Taa

G Gm

齐来献上赞美与歌唱

cai loi hin soeng zaan mei yu go coeng

D A/C\# Bm

彼 此 相爱

bei ci soeng oi

Em A D

愿聚集在此一同高声唱

yun zeoi zaap zoi ci yat tung gou seng coeng"""

RAW['玛丽亚的香膏'] = r"""玛丽亚的香膏 (广)

D key | 70bpm | 4/4

Verse 1

D A/C\# Bm F\#m/A

将我的香膏完全献上给祢

zoeng ngo dik hoeng gou yun qun hin soeng kap nei

G D/F\# Em A

我要用我的全心来爱祢

ngo yiu yoeng ngo dik qun sam loi oi Nei

D A/C\# Bm F\#m/A

将我的香膏完全献上给祢

zoeng ngo dik hoeng gou yun qun hin soeng kap nei

G A D

我要用我的全心来爱祢

ngo yiu yoeng ngo dik qun sam loi oi Nei

Chorus

D A/C\# Bm D/A

我爱 祢主耶穌

ngo oi Nei Ju Ye-Sou

G D/F\# Em A

我爱 祢主耶穌

ngo oi Nei Ju Ye-Sou

D A/C\# Bm D/A

我爱 祢主耶穌

ngo oi Nei Ju Ye-Sou

G A D

我爱祢主耶穌

ngo oi Nei Ju Ye-Sou

Verse 2

将我的生命完全献上给祢

zoeng ngo dik saang ming yun qun hin soeng kap nei

我要用我的一生来爱祢

ngo yiu yoeng ngo dik yat saang loi oi Nei

将我的生命完全献上给祢

zoeng ngo dik saang ming yun qun hin soeng kap nei

我要用我的一生来爱祢

ngo yiu yoeng ngo dik yat saang loi oi Nei"""

RAW['我在这里赞美'] = r"""我在这里赞美 (福)

D key | 140bpm | 4/4

Verse

D

我要赞美救主 你要赞美救主

gua beh oh lo kiu Chu li beh oh lo kiu Chu

A

无论何位何地都要赞美主

bo lun ho wui ho tay long beh oh lo Chu

A

我要赞美救主 你要赞美救主

gua beh oh lo kiu Chu li beh oh lo kiu Chu

A7 D

无论何位何地都要赞美主

bo lun ho wui ho tay long beh oh lo Chu

Chorus x 2

G

赞美主 哈利路亚

oh lo Chu ha li lu ya

D A D

哈利路亚 哈利路亚

ha li lu ya ha li lu ya


我在这里赞美 (广)

D key | 140bpm | 4/4"""

RAW['耶和华祝福满满'] = r"""耶和华祝福满满 (福)

A key | 68bpm | 4/4

Verse

A F\#m Bm E

田中的白鹭丝 无欠缺什么

chan tiong e peng leng si bo khiam kek sia mih

山顶的百合花 春天现香味

sua teng e peh hap hue chun thi hean pang bi

F\#m C\#m D A

总是全能的上帝 每日赏赐真福气

chong si choan leng e Siong-Te mui jit siu su jin hok khi

C\#m F\#m B (Bm) E A

使地上发芽 结实 显出爱疼 的根据

ho tueh chiu huat ge kiat sit hean chut thia thang e kun ki

Chorus

A C\#m

耶和华祝福满满 亲像海边土沙

Ya-Ho-Hua chiok hok mua mua Jin chhiu hai pi tho sua

D E A

恩典慈爱直到万世代

un tian chu ai tit kau ban se tai

A C\#m

我要举手敬拜祂 出欢喜的歌声

goa beh gia chhiu keng pai Yi chhut hua hi e kua sia

D E A

赞美称颂祂名永无息

oh lo cheng siong Yi mia eng bo sua


耶和华祝福满满 (福)

A key | 68bpm | 4/4"""


RAW['我有这喜乐'] = r"""生命在於祢 G Em

我有这喜乐 (福)

G key | 150bpm | 4/4

Verse 1

G G

我有这喜乐 非世界赐给我

goa wu che hee lok hui se kai su hou goa

C C G

我有这喜乐 非世界赐给我

goa wu che hee lok hui se kai su hou goa

G B7 Em

我有这喜乐 非世界赐给我

goa wu che hee lok hui se kai su hou goa

Am7 D G

非世界赐我 非世界所能夺去

hui se kai su goa hui se kai sou eh tek khi

Verse 2

我有这平安 非世界赐给我 x3

goa wu che peng an hui se kai su hou goa

非世界赐我 非世界所能夺去

hui se kai su goa hui se kai sou eh tek khi

Verse 3

我有主耶稣 非世界赐给我 x3

goa wu Chu Ya-So hui se kai su hou goa

非世界赐我 非世界所能夺去

hui se kai su goa hui se kai sou eh tek khi

我有这喜乐 (广)

E key | 150bpm | 4/4

Verse 1

E E

我有这喜乐 非世界赐给我

ngo yau ze hei lok fei sai gaai ci kap ngo

A A E

我有这喜乐 非世界赐给我

ngo yau ze hei lok fei sai gai ci kap ngo

E G\#7 C\#m

我有这喜乐 非世界赐给我

ngo yau ze hei lok fei sai gaai ci kap ngo

F\#m7 B E

非世界赐我 非世界所能夺去

fei sai gai ci ngo fei sai gaai so nang dyut hoi

Verse 2

我有这平安 非世界赐给我 x3

ngo yau ze ping on fei sai gai ci kap ngo

非世界赐我 非世界所能夺去

fei sai gai ci kap ngo fei sai gaai so nang dyut hoi

Verse 3

我有主耶稣 非世界赐给我 x3

ngo yau Ju Ye-Sou fei sai gaai ci kap ngo

非世界赐我 非世界所能夺去

fei sai gai ci kap ngo fei sai gaai so nang dyut hoi"""

RAW['一切歌颂赞美'] = r"""夸胜 (D)

一切歌颂赞美 (福)

D key | 146bpm | 4/4

Intro

|D |D |C |A

Verse

D A G D

一切歌颂赞美 都归我主我的神

yit chet go siong o lo

long kui goa Chu goa e Sin

D Bm C A

祢是配得歌颂与赞美 哈利路亚

Li si pui tek go siong ka o lo ha li lu ya

D D7 G D

我们高声欢呼 高举耶稣之名

nan lang go sia huan ho ko gu Ya So eh mia

D A7 D (A7)

哈\~利路亚

ha li lu ya

Chorus

D D7

赞美主 哈利路亚

o lo Chu ha li lu ya

G D Bm C A

赞美主 哈利路亚 哈 利路亚

o lo Chu ha li lu ya ha li lu ya

D D7

赞美主 哈利路亚

o lo Chu ha li lu ya

G D A7 D

赞美主 哈利路亚 哈 利路亚

o lo Chu ha li lu ya ha li lu ya

一切歌颂赞美 (广)

D key | 146bpm | 4/4

Verse

D A G D

感激基督带领 恩典赐予我未停

gam gik gei duk daai leng

yan dim ci yu ngo mei ting

D Bm C A

日日服事主我心欢喜 哈利路亚

yat yat fook si Ju ngo sam foon hei ha lei lu ya

D D7 G D

让赞美声跨千里 要唱唱唱莫停

yoeng zaan mei seng kwaa cin leoi

yiu coeng coeng coeng mou ting

D A7 D

哈\~利路亚

ha lei lu ya

Chorus

D D7

颂赞祢 哈利路亚

zung zaan Ju ha lei lu ya

G D Bm C A

称赞祢 哈利路亚 哈 利路亚

ceng zaan Ju ha lei lu ya ha lei lu ya

D D7

颂赞祢 哈利路亚

zung zaan Ju ha lei lu ya

G D A D

称赞祢 哈利路亚 哈利路亚

ceng zaan Ju ha lei lu ya ha lei lu ya"""

RAW['一生爱祢'] = r"""一生爱祢 (福)

D key | 70bpm | 4/4

Verse

D G

亲爱的宝贵耶稣

qin ai e bo gui Ya-So

Em Asus4 A

祢爱何等的甘甜

Li ai ho teng e gam di

F\#m Bm

我的心深深被祢吸引

goa e sim chim chim hor Li kip yin

Em A D G/A

爱祢是我的喜乐

ai Li si goa e hee lok

Chorus

D F\# Bm Am

一生爱祢 一生敬拜祢

yit seng ai Li yit seng keng bai Li

D7 G Em A

一生爱祢 一生荣耀祢

yit seng ai Li yit seng eng yao Li

F\#m Bm

一生奉献 一生不回头

yit seng hong hean yit seng boh huey tau

Em A D

一生爱祢跟随祢

yit seng ai Li gun tueh Li

一生爱祢 (广)

E key | 70bpm | 4/4

Verse

E A

亲爱的宝贵耶稣

can oi dik bou gwai Ye-Sou

F\#m Bsus4 B

祢爱何等的甘甜

Nei oi ho dang dik gam tim

G\#m C\#m

我的心深深被祢吸引

ngo dik sam sam sam bei Nei kap yan

F\#m B E A/B

爱祢是我的喜乐

oi Nei si ngo dik hei lok

Chorus

E G\# C\#m Bm

一生爱祢 一生敬拜祢

yat saang oi Nei yat saang ging baai Nei

E7 A F\#m B

一生爱祢 一生荣耀祢

yat saang oi Nei yat saang wing yiu Nei

G\#m C\#m

一生奉献 一生不回头

yat saang fung hin yat saang bat wui tau

F\#m B E

一生爱祢跟随祢

yat saang oi Nei gan ceoi Nei"""

RAW['永远爱祢'] = r"""恳求主

永远爱祢 (福)

D key | 70bpm | 4/4

Verse

D A/C\# Bm7

祢是我心所渴慕

Li si goa sim so kek bo

Em7 Em7/D A/C\#

祢是我心 所爱

Li si goa sim so ai

F\#sus4 F\# Bm7 E

在我生命中只有祢

ti goa xi mia tiong ji wu Li

D/A A D

是我所爱 哦主

si goa so ai oh Chu

Chorus

D2 Bm7

我要永远爱祢耶稣

goa beh eng wan ai Li Ya-So

Em7 G/A

单单爱祢 深深爱祢

dan dan ai Li chim chim ai Li

D2 Bm7

我要永远爱祢耶稣

goa beh eng wan ai Li Ya-So

Em7 G/A D

单单爱祢 我主

dan dan ai Li goa Chu

永远爱祢 (广)

D key | 70bpm | 4/4

Verse

D A/C\# Bm7

祢是我心所渴慕

Nei si ngo sam so hot mou

Em7 Em7/D A/C\#

祢是我心 所爱

Nei si ngo sam so oi

F\#sus4 F\# Bm7 E

在我生命中只有祢

zoi ngo saang ming zung zek yau Nei

D/A A D

是我所爱 哦主

si ngo so oi oh Ju

Chorus

D2 Bm7

我要永远爱祢耶稣

ngo yiu wing yun oi Nei Ye Sou

Em7 G/A

单单爱祢 更深爱祢

daan daan oi Nei gaang sam oi Nei

D2 Bm7

我要永远爱祢耶稣

ngo yiu wing yun oi Nei Ye Sou

Em7 G/A D

单单爱祢 我主

daan daan oi Nei ngo Ju"""

RAW['奉主耶稣圣名'] = r"""降下祢恩雨(Rain Down) (C)

奉主耶稣圣名 (福)

D key | 150bpm | 4/4

Verse

D D

奉主耶稣圣名祝你喜乐

hong Chu Ya So seng mia jiok li hee lok

G D/F\# E A

奉主耶稣圣名祝你平安

hong Chu Ya So seng mia jiok li peng an

D G Gm

奉主耶稣圣名祝你健康

hong Chu Ya So seng mia jiok li kian kong

G D/F\# Em A D

奉主耶稣圣名祝你 刚强

hong Chu Ya-So seng mia jiok li kian keong

Chorus

D D

阿～～们 阿～～们

ah men

A D A D

阿～～们 阿～们 阿～们

奉主耶稣圣名 (广)

D key | 150bpm | 4/4

Verse

D D

奉主耶稣圣名祝你喜乐

fung Ju Ye-Sou sing meng zuk nei hei lok

G D/F\# E A

奉主耶稣圣名祝你平安

fung Ju Ye-Sou sing meng zuk nei ping on

D G Gm

奉主耶稣圣名祝你健康

fung Ju Ye-Sou sing meng zuk nei gin hong

G D/F\# Em A D

奉主耶稣圣名祝你 刚强

fung Ju Ye-Sou sing meng zuk Nei gong koeng

Chorus

D D

阿～～们 阿～～们

ah men

A D A D

阿～～们 阿～们 阿～们"""

RAW['和撒那'] = r"""和撒那 (广)

F key | 133bpm | 4/4

Verse 1

|F |C |Bb |C

和撒那 和撒那

Ho-sa-na Ho-sa-na

和撒那归万王之王

Ho-sa-na gwai maan wong zi wong

和撒那 和撒那

Ho-sa-na Ho-sa-na

和撒那归万主之主

Ho-sa-na gwai maan Ju zi Ju

Chorus

Bb C F Bb C F

主我高举祢名 心中感恩赞美

Ju ngo gou geoi Nei meng

sam zung gam yan zaan mei

Bb C F C/E Dm

我尊崇祢我主 我 神

ngo jun sung ne ingo Ju ngo San

Bb C F

和撒那归万王之王

Ho-sa-na gwai maan wong zi wong

和撒那 (广)

E key | 133bpm | 4/4

Verse 1

E B

和撒那 和撒那

Ho-sa-na Ho-sa-na

A B

和撒那归万王之王

Ho-sa-na gwai maan wong zi wong

E B

和撒那 和撒那

Ho-sa-na Ho-sa-na

A B

和撒那归万主之主

Ho-sa-na gwai maan Ju zi Ju

Chorus

A B E A B E

主我高举祢名 心中感恩赞美

Ju ngo gou geoi Nei meng

sam zung gam yan zaan mei

A B E B/D\# C\#m

我尊崇祢我主 我 神

ngo jun sung nei ngo Ju ngo San

A B E

和撒那归万王之王

Ho-sa-na gwai maan wong zi wong"""

RAW['神就是爱'] = r"""A E/G\#

神就是爱 (广)

C key | 140bpm | 4/4

Verse x 2

C Csus4

赞美 用心灵赞美

zan mei yung sam leng zan mei

Dm F G

敬拜 用心灵敬拜

ging bai yung yung sam leng ging bai

Chorus

F G Em Am

万王之王 万主之主

man wong zi wong man Ju zi Ju

Dm G C Dm Em

神祂是光 祂光照我的心

San Ta si gwong Ta gwong ziu ngo dik sam

F G Em Am

神祂是爱 用宝血洗净我

San Ta si oi yung bou hyut sai zing ngo

Dm G C

我们相爱 因祂先爱我们

ngo mun soeng oi yan Ta sin oi ngo mun

神就是爱 (福)

C key | 140bpm | 4/4

Verse x 2

C Csus4

赞美 用心灵赞美

oh lo eng sim leng oh lo

Dm F G

敬拜 用心灵敬拜

keng bai eng sim leng keng bai

Chorus

F G Em Am

万王之王 万主之主

ban ong zi Ong ban chu zi Chu

Dm G C Dm Em

神祂是光 祂光照我的心

Sin tio si kng Yi kng jio goa e sim

F G Em Am

神祂是爱 用宝血洗净我

Sin tio si ai eng bo huey soe jeng goa

Dm G C

我们相爱 因祂先爱我们

Nan lang siong ai yin Yi sin ai nan lang"""

RAW['我一心称谢主'] = r"""我一心称谢主 (广)

D key | 67bpm | 4/4

Verse 1

D A/C\# Bm D/A G A D

我一心称谢主 传扬祢的作为

ngo yat sam cing ze Ju

cyun yoeng Nei dik zok wai

G A/G D A/C\# Bm

至高者 我要因祢欢喜快乐

Zi Gou Ze ngo yiu yan Nei foon hei faai lok

Em E A

我要歌颂祢的圣名

ngo yiu go zung Nei dik sing meng

Verse 2

D A/C\# Bm D/A G A D

我一心称谢主 传扬祢的作为

ngo yat sam cing ze Ju

cyun yoeng Nei dik zok wai

G A/G D A/C\# Bm

至高者 我要因祢欢喜快乐

Zi Gou Ze ngo yiu yan Nei foon hei faai lok

Em A D

哈利 路 亚

ha lei lu ya

Chorus (2x)

G A/G F\#m (F\#) Bm

我要歌颂主祢奇妙的圣名

ngo yiu go zung Ju Nei

kei miu dik sing meng

Em A D (Em D/F\#)

哈利 路 亚

ha lei lu ya

我一心称谢主 (福)

D key | 67bpm | 4/4

Verse 1

D A/C\# Bm D/A G A D

我一心称谢主 传扬祢的作为

goa yit sim ceng sia Chu

zhuan yong Li e jiok wui

G A/G D A/C\# Bm

至高者 我要因祢欢喜快乐

Chee Ko Chia goa bei yin Li hua hee kwai lok

Em E A

我要歌颂祢的圣名

goa beh ko siong Li e seng mia

Verse 2

D A/C\# Bm D/A G A D

我一心称谢主 传扬祢的作为

goa yit sim ceng sia Chu

zhuan yong Li e jiok ui

G A/G D A/C\# Bm

至高者 我要因祢欢喜快乐

Chi Ko Chia goa bei yin Li hua hee kwai lok

Em A D

哈利 路 亚

ha li lu ya

Chorus (2x)

G A/G F\#m (F\#) Bm

我要歌颂主祢奇妙的圣名

goa beh go siong Chu Li ki biao e seng mia

Em A D (Em D/F\#)

哈利 路 亚

ha li lu ya"""

RAW['耶稣我爱祢'] = r"""生命在於祢 G Em

耶稣我爱祢 (福)

C key | 68bpm | 4/4

Verse

C F Dm7 G C

耶稣我爱祢 我跪 在祢面前

Ya-So goa ai Li goa gui ti Li bin zyeng

C F Dm7 G C

赞美敬拜祢 主 我 的王

o lo geng bai Li Chu goa ong

Chorus

Am7 Dm7 F G C

哈利 路亚 哈 利 路亚

ha-li-lu-ya ha-li-lu-ya

Am7 Dm7 F G C

哈利 路亚 哈 利 路

ha-li-lu-ya ha-li-lu-ya

耶稣我爱祢 (福)

Bb key | 68bpm | 4/4

Verse

Bb Eb Cm7 F Bb

耶稣我爱祢 我跪 在祢面前

Ya-So goa ai Li goa gui ti Li bin zyeng

Bb Eb Cm7 F Bb

赞美敬拜祢 主 我 的王

o lo geng bai Li Chu goa ong

Chorus

Gm7 Cm7 Eb F Bb

哈利 路亚 哈 利 路亚

ha-li-lu-ya ha-li-lu-ya

Gm7 Cm7 Eb F Bb

哈利 路亚 哈 利 路

ha-li-lu-ya ha-li-lu-ya"""

RAW['爱到永远'] = r"""爱我到永远 (福)

A key | 74bpm | 4/4

Verse

E G\#m

祢从头起就知道我的样

Li dui tau ki tio zai ia goa e kuan

C\#m G\#m

但是不曾听过祢嫌我麻烦

dan si mm bat tia koe Li hiam ngo ma huan

F\#m G\#m

祢最清楚我是怎么样的人

Li siung cing co ngo si an zhua kuan e lang

F\#m B

但是不曾讲离开我不管

dan si mm bat gong li kuey goa bo guan

Pre-chorus

C\#m G\#m A B

祢的心不改变 祢的爱到永远

Li e sim beh gai bian Li e ai kau eng guan

Chorus

E C\#m

若无力走 有祢来背

na bo lat kia wu li lai ia

A B

若看不到 有祢来牵

na kua beh tio wu li lai khan

C\#m G\#m

祢在身边 我不怕暗

Li ti sin bin goa bo kia an

A B

我找不到另外一个

goa chuey beh tio leng guai jit ko

E

那样爱我的人

ah neh ai goa e lang

爱我到永远 (福)

G key | 74bpm | 4/4

Verse

G Bm

祢从头起就知道我的样

Li dui tau ki tio zai ia goa e kuan

Em Bm

但是不曾听过祢嫌我麻烦

dan si mm bat tia koe Li hiam ngo ma huan

Am Bm

祢最清楚我是怎么样的人

Li siung cing co ngo si an zhua kuan e lang

Am D

但是不曾讲离开我不管

dan si mm bat gong li kuey goa bo guan

Pre-chorus

Em Bm C D

祢的心不改变 祢的爱到永远

Li e sim beh gai bian Li e ai kau eng guan

Chorus

G Em

若无力走 有祢来背

na bo lat kia wu li lai ia

C D

若看不到 有祢来牵

na kua beh tio wu li lai khan

Em Bm

祢在身边 我不怕暗

Li ti sin bin ngo bo kia an

C D

我找不到另外一个

goa chuey beh tio leng guai jit ko

G

那样爱我的人

ah neh ai goa e lang"""

RAW['祷告主 仰望主'] = r"""祷告主 仰望主 (福)

D key | 68bpm | 4/4

Verse

D Em

祷告主 仰望主

khi toh Chu yong bong Chu

A D

祂是我拯救我力量

Yi si goa cheng kiu goa lat liong

D/F\# G

敬畏主 荣耀主

keng wue Chu eng yao Chu

A D

祂是我性命的保障

Yi si goa si mia e po chiong

Chorus

D A D

祂是我亮光 是我的力量

Yi si goa liong kng si goa e lat liong

Em A

祂是我性命的保障

Yi si goa si mia e po chiong

D A D

我愿仰望祂 赞美耶和华

goa goan yong bong Yi

oh lo Ya-Ho-Hoa

Em A D

我心要歌颂赞美祂

goa sim beh ko siong oh lo Yi

祷告主 仰望主 (广)

D key | 68bpm | 4/4

Verse

D Em

祷告主 仰望主

tou gou Ju yoeng mong Ju

A D

祂是我拯救我力量

Taa si ngo cing gau ngo lik loeng

D/F\# G

敬畏主 荣耀主

ging wai Ju wing yiu Ju

A D

祂是我性命的保障

Taa si ngo seng meng dik bou zoeng

Chorus

D A D

祂是我亮光 是我的力量

Taa si ngo loeng gwong

si ngo dik lik loeng

Em A

祂是我性命的保障

Taa si ngo seng meng dik bou zoeng

D A D

我愿仰望祂 赞美耶和华

ngo yun yoeng mong Taa

zaan mei Ye-Wo-Waa

Em A D

我心要歌颂赞美祂

ngo sam yiu go zung zaan mei Taa"""

RAW['感谢感谢耶稣'] = r"""感谢感谢耶稣 (广)

D key | 105bpm | 4/4

Verse 1

D G D

感谢感谢耶稣 感谢感谢耶稣

gam ze gam ze Ye Sou (2x)

D A

感谢感谢耶稣在我心

gam ze gam ze Ye sou zoi ngo sam

G D Em D/F\#

感谢感谢耶稣 感谢感谢耶稣

gam ze gam ze Ye Sou (2x)

G A D

感谢感谢耶稣在我心

gam ze gam ze Ye Sou zoi ngo sam

Verse 2

赞美救主耶稣 赞美救主耶稣

zaan mei Gau Ju Ye Sou (2x)

赞美救主耶稣在我心

zaan mei Gau Ju Ye Sou zoi ngo sam

Verse 3

荣耀哈利路亚 荣耀哈利路亚

wing yiu ha lei lu ya (2x)

荣耀哈利路亚赞美主

wing yiu ha lei lu ya zaan mei Ju

感谢感谢耶稣 (福)

F key | 105bpm | 4/4

Verse 1

F Bb F

感谢感谢耶稣 感谢感谢耶稣

gam sia gam sia Ya So (2x)

F C

感谢感谢耶稣在我心

gam sia gam sia Ya So ti goa sim

Bb F Gm F/A

感谢感谢耶稣 感谢感谢耶稣

gam sia gam sia Ya So x 2

Bb C F

感谢感谢耶稣在我心

gam sia gam sia Ya So ti goa sim

Verse 2

赞美救主耶稣 赞美救主耶稣

o loh kiu Chu Ya So

赞美救主耶稣在我心

o loh kiu Chu Ya So ti goa sim

Verse 3

荣耀哈利路亚 荣耀哈利路亚

eng yao ha li lu ya

荣耀哈利路亚赞美主

eng yao ha li lu ya o lo Chu"""

RAW['感谢耶稣'] = r"""感谢耶稣 (广)

C key | 70bpm | 4/4

Verse

C Dm G7 C

感谢耶稣 赐给我大爱

gam ze Ye Sou ci kap ngo daai oi

Dm G7 C C7

感谢耶稣 白白赐救恩

gam ze Ye Sou baak baak ci gau yan

Chorus x 2

F G

我要高声赞美主名

ngo yiu gou seng zaan mei Ju ming

C G/B Am

日夜不停赞美祂

yat ye bat ting zaan mei Taa

Dm G7

祂是我一切

Taa si ngo yat cai

C (Dm Em)

祂是我主

Taa si ngo Ju

感谢耶稣 (福)

C key | 70bpm | 4/4

Verse

C Dm G7 C

感谢耶稣 赐给我大爱

kam sia Ya So su ho goa doa ai

Dm G7 C C7

感谢耶稣 白白赐救恩

kam sia Ya So peh peh su kiu un

Chorus x 2

F G

我要高声赞美主名

goa beh ko sia oh lo Chu mia

C G/B Am

日夜不停赞美祂

jit mi bo theng oh lo Yi

Dm G7

祂是我一切

Yi si goa yit chiat

C (Dm Em)

祂是我主

Yi si goa Chu"""

RAW['哈利路亚'] = r"""哈利路亚 (福)

Am key | 68bpm | 4/4

Verse

|Am |C

哈利路亚 哈利路亚

ha li lu ya ha li lu ya

|Dm G |Am

我心敬拜祢上帝

goa sim keng bai Li siong tei

Chorus

|F |C Am

我要感谢祢 我要赞美祢

goa beh gam xia Li goa beh oh lo Li

|Dm G |Am

祢是良善的神

Li si liong sian e Sin

我要感谢祢 我要赞美祢

goa beh gam xia Li goa beh oh lo Li

祢是慈爱的神

Li si zu ai e Sin

哈利路亚 (福)

Bm key | 68bpm | 4/4

Verse

|Bm |D

|Em A |Bm

哈利路亚 哈利路亚

ha li lu ya ha li lu ya

我心敬拜祢上帝

goa sim keng bai Li siong tei

Chorus

|G |D Bm

|Em A |Bm

我要感谢祢 我要赞美祢

goa beh gam xia Li goa beh oh lo Li

祢是良善的神

Li si liong sian e Sin

我要感谢祢 我要赞美祢

goa beh gam xia Li goa beh oh lo Li

祢是慈爱的神

Li si zu ai e Sin"""

RAW['哈利路亚来赞美主'] = r"""哈利路亚来赞美主 (福)

Cm key | 128bpm | 4/4

Verse

Cm Fm

哈利路亚来赞美主

ha-li-lu-ya lai oh lo Chu

Cm G7

哈利路亚来赞美主

ha-li-lu-ya lai oh lo Chu

Cm Fm

哈利路亚来赞美主

ha-li-lu-ya lai oh lo Chu

Cm G7 Cm

哈利路亚赞美耶稣我的主

ha-li-lu-ya oh lo Ya-So goa e Chu

Chorus

Fm Cm

我向我的主高举双手

goa hiong goa e Chu ko gu siang chiu

G7 Cm C

向我的主屈膝敬拜

hiong goa e Chu gui loh keng bai

Fm Cm

我向我的主高举双手

goa hiong goa e Chu ko gu siang chhiu

G7 Cm

向我的主敬拜

hiong goa e Chu keng bai

哈利路亚来赞美主 (广)

Dm key | 128bpm | 4/4

Verse

Dm Gm

哈利路亚来赞美主

ha lei lu ya loi zaan mei Ju

Dm A7

哈利路亚来赞美主

ha lei lu ya loi zaan mei Ju

Dm Gm

哈利路亚来赞美主

ha lei lu ya loi zaan mei Ju

Dm A7 Dm

哈利路亚赞美耶稣我的主

ha lei lu ya loi zaan mei Ye Sou ngo dik Ju

Chorus

Gm Dm

我向我的主高举双手

ngo hoeng ngo dik Ju gou goi soeng sau

A7 Dm D

向我的主屈膝敬拜

hoeng ngo dik Ju wat sat ging baai

Gm Dm

我向我的主高举双手

ngo hoeng ngo dik Ju gou goi soeng sau

A7 Dm

向我的主敬拜

hoeng ngo dik Ju ging baai"""

RAW['基督耶稣来作伴'] = r"""基督耶稣来作伴 (福)

A key | 70bpm | 4/4

Verse 1

A C\#m7

主耶稣引导阮的脚步

Chu Ya-So yin choa guan e ka po

D E/D A

亲像灯照人生的路途

chin chiu ding jio lin seng e lo tor

F\#m7 C\#m7

无论风有外大 无论雨有外寒

bo lun hong wu lua dua bo lun ho wu lua gua

Bm7 (E) E (A)

阮一生决心要随祂行

guan yit sing gua sim beh tueh Yi gia

Verse 2

祂的爱阮放在心肝内

Yi e ai guan keng teh sim gua lai

有耶稣的人心内会知

wu Ya-So e lang sim lai eh zai

无论人按怎看 阮的心没变卦

bo lun lang an zua kua guan e sim buey ben gua

靠耶稣咱生活着快活

ko Ya-So lan sing wa tio kui wa

Chorus

A F\#m7

咱的心免着惊 基督耶稣来作伴

lan e sim mian tio kia Ki-Tok Ya-So lai zhuey phoa

D E

有困难祂拢嘛会知影

wu kun lan Yi long ma eh zai yia

A F\#m7

咱的心免着惊 基督耶稣来作伴

lan e sim mian tio kia Ki-Tok Ya-So lai zhuey phoa

D E A

为祂唱出感恩的歌声

wui Yi qiu chut gam wun e gua sia"""

RAW['靠我主耶稣'] = r"""靠我主耶稣 (广)

E key | 140bpm | 4/4

Verse

E B E

靠我主耶稣 我们与神和好

kau ngo Ju Ye-Sou ngo mun yu San wo hou

E7 E B

靠我主耶稣 我们与神和好

kau ngo Ju Ye-Sou ngo mun yu San wo hou

Chorus

E C\#m

在盼望里喜乐

zoi pan mong loi hei lok

F\#m B B7

享受神的荣耀

hoeng sau San dik wing yiu

E B E

靠我主耶稣 我们与神和好

kau ngo Ju Ye-Sou ngo mun yu San wo hou

靠我主耶稣 (福)

F key | 140bpm | 4/4

Verse

F C7 F

靠我主耶稣 我们与神和好

ko goa Chu Ya-So lan lang ka Sin ho ho

F F7 C

靠我主耶稣 我们与神和好

ko goa Chu Ya-So lan lang ka Sin ho ho

Chorus

F Dm

在盼望里喜乐

ti pan bong lai hee lok

Gm C C7

享受神的荣 耀

hiong siu Sin e eng yao

F C F

靠我主耶稣 我们与神和好

ko goa Chu Ya-So lan lang ka Sin ho ho"""

RAW['祢的慈爱比生命更好'] = r"""祢的慈爱比生命更好 (广)

D key | 140bpm | 4/4

Verse 1

D Em7

主祢的慈爱比生命更好

Ju Nei dik ci ngoi bei saang ming gang hou

A D

主祢的慈爱比生命更好

Ju Nei dik ci ngoi bei saang ming gang hou

D D7 G

我要用嘴唇 来赞美祢

ngo yiu yung zeoi seon loi zaan mei Nei

D A7 D

因祢的慈爱比生命更好

yan Nei dik ci ngoi bei saang ming gang hou

Verse 2

我要奉祢名来举起我手

ngo yiu fung Nei ming loi geoi hei ngo sau

我要奉祢名来举起我手

ngo yiu fung Nei ming loi geoi hei ngo sau

我要用嘴唇来赞美祢

ngo yiu yung zeoi seon loi zaan mei Nei

因祢的慈爱比生命更好

yan Nei dik ci ngoi bei saang ming gang hou

祢的慈爱比生命更好 (福)

C key | 140bpm | 4/4

Verse 1

C Dm7

主祢的慈爱比生命更好\~

Chu Li e zu ai bi si mia ka ho

G C

主祢的慈爱比生命更好

Chu Li eh zu ai bi si mia ka ho

C C7 A

我要用嘴唇 来赞美祢\~

goa beh eng cui dun lai oh loh Li\~

C G7 C

因祢的慈爱比生命更好

yin Li e zu ai bi xi mia kah ho

Verse 2

我要奉祢名来举起我手

goa beh hong Li mia lai gia ki goa chiu

我要奉祢名来举起我手

goa beh hong Li mia lai gia ki goa chiu

我要用嘴唇来赞美祢\~

goa beh eng cui dun lai oh loh Li\~

因祢的慈爱比生命更好

yin Li e zu ai bi xi mia kah ho"""

RAW['主祢的慈爱比生命更好'] = RAW['祢的慈爱比生命更好']

RAW['轻轻听'] = r"""轻轻听 (福)

D key | 68bpm | 4/4

Verse

D Bm

轻轻听 我要轻轻听

khin khin thia goa beh khin khin thia

G A D

我要专心听我主的声

goa bei zuan sim thia goa Chu e sia

D Bm

轻轻听 祂在轻轻听

khin khin thia Yi tei khin khin thia

G A D

我的牧人认得我的声

goa e bok lin lin tiok goa sia

Chorus

F\#m Bm

祂是大牧者 祂知我的名

Yi si dua bok jia Yi zai goa e mia

G A D

我一生要听主的声

goa yit seng ai tia Chu e sia

F\#m Bm

祂是大牧者 保守我生命

Yi si dua bok jia po siu goa xi mia

G A D

祂的羊认得祂的声

Yi e ngiu lin tio Yi e sia

轻轻听 (广)

Bb key | 68bpm | 4/4

Verse

C Am

细细听 轻轻细细听

sai sai ting heng heng sai sai ting

F G C

倾听祢说话儿共对应

king ting Nei syut waa ngai gung deoi ying

C Am

细细说 轻轻细细说

sai sai syut heng heng sai sai syut

F G C

因知道我牧人在细听

yan zi dou ngo muk yan zoi sai ting

Chorus

Em Am

上帝祢是我独一生命光

Soeng Dai Nei si ngo duk yat saang ming gwong

F G C

羊属祢必清楚听祢声

yoeng suk Nei bit cing co ting Nei seng

Em Am

牧养引导我轻声教导我

muk yoeng yan dou ngo heng seng gaau dou ngo

F G C

一生听祢话儿共对应

yat saang ting Nei waa ngai gung deoi ying"""

RAW['奇妙双手'] = r"""奇妙的双手 (广)

D key | 132bpm | 4/4

Verse

|Bm |G |Bm |Bm

|Bm |G |Bm |A

一双手为我 将祝福赐下

yat soeng sau wai ngo zoeng zuk fook ci haa

恩光今天心中照亮

yan gwong gam tin sam zung ziu loeng

活着没罪担 枷锁都脱落

wut zoek mut zoi daam gaa so dou tyut lok

义路乐意走上

yi lou lok yi zau soeng

Pre-chorus / Coda

D G

身心得拯救 抛开苦与忧

san sam dak cing gau paau hoi fu yu yau

D A

靠祢奇妙双手

kaau Nei kei miu soeng sau

G D Bm

高山可迁走 祢爱不变旧

gou saan ho cin zau Nei oi bat bin gau

Em A D

有祢一生快乐透

yau Nei yat saang faai lok tau

Chorus

G Bm G D A

是 祢 一双恩手救赎我

si Nei yat soeng yan sau gau suk ngo

是 祢 一双恩手祝福我

si Nei yat soeng yan sau zuk fook ngo

奇妙的双手 (广)

Bb key | 132bpm | 4/4

Verse

|Gm |Eb |Gm |Gm

|Gm |Eb |Gm |F

一双手为我 将祝福赐下

yat soeng sau wai ngo zoeng zuk fook ci haa

恩光今天心中照亮

yan gwong gam tin sam zung ziu loeng

活着没罪担 枷锁都脱落

wut zoek mut zoi daam gaa so dou tyut lok

义路乐意走上

yi lou lok yi zau soeng

Pre-chorus / Coda

Bb Eb

身心得拯救 抛开苦与忧

san sam dak cing gau paau hoi fu yu yau

Bb F

靠祢奇妙双手

kaau Nei kei miu soeng sau

Eb Bb Gm

高山可迁走 祢爱不变旧

gou saan ho cin zau Nei oi bat bin gau

Cm F Bb

有祢一生快乐透

yau Nei yat saang faai lok tau

Chorus

Eb Gm Eb Bb F

是 祢 一双恩手救赎我

si Nei yat soeng yan sau gau suk ngo

是 祢 一双恩手祝福我

si Nei yat soeng yan sau zuk fook ngo"""

RAW['求主充满我'] = r"""求主充满我 (广)

D key | 68bpm | 4/4

Verse

|D |A/C\# |Bm |Bm

|G |A |D |D

主我来寻求祢的面

Ju ngo loi cam kau Nei dik min

求祢充满我 来充满我

kau Nei cung mun ngo loi cung mun ngo

主我渴慕祢的同在

Ju ngo hot mou Nei tong zoi

求祢洁净我 来充满我

kau Nei git zeng ngo loi cung mun ngo

Chorus

D A/C\# G/B D/A

耶稣 耶稣 耶稣 耶稣

Ye-Sou Ye-Sou Ye-Sou Ye-Sou

G D/F\# E A7

祢的宝血洗净我

Nei dik bou hyut git zeng ngo

D A/C\# G/B D/A

耶稣 耶稣 耶稣 耶稣

Ye-Sou Ye-Sou Ye-Sou Ye-Sou

G D/F\# Em A7 D

祢以恩典为我 冠 冕

Nei yi yan din wai ngo gun min

求主充满我 (福)

D key | 68bpm | 4/4

Verse

|D |A/C\# |Bm |Bm

|G |A |D |D

主我来寻求祢的面

Chu goa lai chim kiu Li e bin

求祢充满我 来充满我

kiu Li chiong mua goa ai chiong mua goa

主我渴慕祢的同在

Chu goa kek bo Li e dang zai

求祢洁净我 来充满我

kiu Li kian cheng goa lai chiong mua goa

Chorus

D A/C\# G/B D/A

耶稣 耶稣 耶稣 耶稣

Ya-So Ya-So Ya-So Ya-So

G D/F\# E A

祢的宝血洗净我

Li e bo hueh soe cheng goa

D A/C\# G/B D/A

耶稣 耶稣 耶稣 耶稣

Ya-So Ya-So Ya-So Ya-So

G D/F\# Em A D

祢以恩典为我 冠 冕

Li yi un dian wui goa guan bian"""

RAW['若是有祢在我的生命'] = r"""若是有祢在我的生命 (福)

A key | 66bpm | 3/4

Verse

A F\#m D E

若是有祢伫我的生命 我就永远不惊惶

na si wu Li ti goa e si mia

goa tio eng wan bueh khia hia

D A//C\#

风雨那呢大 旷野这呢阔

hong ho an neh toa kong yiak chia ni khoah

Bm E

有祢同在无摇泏

wu Li tang zai bo yio choah

A F\#m D E

若是有祢伫我的生命 我就永远不孤单

na si wu Li ti goa e si mia

goa tio eng wan bueh ko thoa

D A//C\#

有祢相作伴 与祢逗阵行

wu Li sa choe phoa kah Li tau tin khia

Bm E A

充满温暖不畏寒

chiong moa wun loan bueh wui koa

Chorus

A E/G\# F\#m C\#m

海水会干 石头会烂 祢的爱疼无变换

hai chui eh ta chioh tau eh noa

Li e thia thang bo bian woa

D A/C\# Bm B7 E

甘愿为我 受尽拖磨 将我当作祢心肝

kam goan wui goa siu ching thoa boa

chiong goa tng choe Li sim koa

A E/G\# F\#m C\#m

海水会干 石头会烂 祢的爱疼无变换

hai chui eh ta chioh tau eh noa

Li e thia thang bo bian woa

D A/C\# Bm E A

恩情这大 怎样感谢 一生与主连相倚

wun cheng chia toa cha yiu kam sia

yit seng ka Chu liam sio woa"""

RAW['上帝是我们的避难所'] = r"""上帝是我们的避难所 (广)

Bb key | 70bpm | 4/4

Verse

Bb Dm

上帝是我们的避难所

Soeng Dai si ngo mun dik bei naan so

Eb F

是我们的力量

si ngo mun dik lik loeng

Bb F/A Gm Eb

是我们在患难中

si ngo mun zoi wang naan zung

Cm F Bb

随时的帮助

soi si dik bong zo

Chorus

Eb Bb/D Gm

哈利路亚 哈利路亚

ha lei lu ya ha lei lu ya

Cm F Bb Bb7

我要歌颂祂

ngo yiu go zung Taa

Eb Bb/D Gm

哈利路亚 哈利路亚

ha lei lu ya ha lei lu ya

Cm F Bb

我要赞美祂

ngo yiu zaan mei Taa

上帝是我们的避难所 (福)

D key | 70bpm | 4/4

Verse

D F\#m

上帝是我们的避难所

Siong-Tei si lan lang e pi lan so

G A

是我们的力量

si lan lang e lat liong

D A/C\# Bm G

是我 们在患难中

si lan lang teh hoan lan tiong

Em A D

随时的帮助

sui si e pang zo

Chorus

|G |D Bm

|Em A |D

哈利路亚 哈利路亚

ha li lu ya ha li lu ya

我要歌颂祂

goa beh ko siong Yi

哈利路亚 哈利路亚

ha li lu ya ha li lu ya

我要赞美祂

goa beh oh lo Yi"""

RAW['我的上帝我的王啊'] = r"""我的上帝 (广)

Am key | 140bpm | 4/4

Verse x 2

Am Am

我的上帝 我的王啊

ngo dik Soeng Dai ngo dik Wong ah

F G Am

我要尊崇祢

ngo yiu jun sung Nei

Chorus x 2

F Am F G Am

我要永永远远称颂祢的名

ngo yiu wing wing yun yun cing zung Nei dik meng

我的上帝 (福)

Am key | 140bpm | 4/4

Verse x 2

Am Am

我的上帝 我的王啊

goa eh Siong tei goa eh Ong ah

F G Am

我要尊崇祢

goa beh jun chong Li

Chorus x 2

F Am F G Am

我要永永远远称颂祢的名

goa beh eng eng guan guan cheng siong Li eh mia"""

RAW['我的上帝我的王'] = RAW['我的上帝我的王啊']

RAW['我的心赞美主耶稣'] = r"""我的心赞美主耶稣 (福)

C key | 70bpm | 4/4

Verse

C G C

我的心赞美主耶稣

goa e sim o-lo Chu Ya-So

Dm D G

赞美祂无限的爱

o-lo Yi bo han e ai

F C/E Em Am

我的手要高举 我的口要赞美

goa e chhiu beh ko khi goa e chhui beh o-lo

Dm G C

我心 我心 归于祂

goa sim goa sim kui ho Yi

Chorus

F C/E F G

祂是我的磐石 祂是我的拯救

Yi si goa e phoa chioh Yi si goa e cheng kiu

C C/E

我的心啊 你要

goa e sim ah li beh

F C

称颂赞美祂圣名

cheng siong oh lo Yi seng mia

Dm G C

我心 我心 赞美祂

goa sim goa sim oh lo Yi

我的心赞美主耶稣 (广)

A key | 70bpm | 4/4

Verse

A E A

我的心 赞美主耶稣

ngo dik sam zaan mei Ju-Ye-Sou

Bm B E

赞美祂无限的爱

zaan mei Taa mou hann dik oi

D E C\#m F\#m

我的手要高举 我的口要赞美

ngo dik sau yiu gou geoi

ngo dik hau yiu zaan mei

Bm E A

我心 我心 归于祂

ngo sam ngo sam gwai yu Taa

Chorus

D A/C\# D E

祂是我的磐石 祂是我的拯救

Taa si ngo dik pun sek Taa si ngo dik cing kau

A A/C\#

我的心啊 你要

ngo dik sam ah nei yiu

D A/C\#

称颂赞美祂圣名

cing zung zaan mei Taa sing meng

Bm E A

我心 我心 赞美祂

ngo sam ngo sam zaan mei Taa"""

RAW['我的神我要敬拜祢'] = r"""我的神我要敬拜祢 (广)

C key | 68bpm | 4/4

Verse

C Dm C

我的神 我要敬拜祢

ngo dik San ngo yiu ging baai Nei

F G

我的心深深地爱祢

ngo dik sam sam sam dei ngoi Nei

Am Dm C Am

在祢的脚前 我要来思想祢

zoi Nei dik goek cin ngo yiu loi si soeng Nei

G Dm C

我的心赞美敬拜祢

ngo dik sam zaan mei ging baai Nei

Chorus

Am G

祢是我心灵的满足

Nei si ngo sam ling dik mun zuk

Am G

祢是我唯一的喜乐

Nei si ngo wai yat dik hei lok

Am Dm C Am

在祢的脚前 我思想祢恩典

zoi Nei dik goek cin ngo si soeng Nei yan din

G Dm C

我的神我要敬拜祢

ngo dik San ngo yiu ging baai Nei

我的神我要敬拜祢 (福)

D key | 70bpm | 4/4

Verse

D Em D

我的神 我要敬拜祢

goa e Sin goa beh keng bai Li

G A

我的心深深地爱祢

goa e sim chim chim e ai Li

Bm Em D Bm

在祢的脚前 我思想祢恩典

ti Li e ka zhyeng goa su siung Li wun dian

A Em D

我的心 赞美敬拜祢

goa e sim oh lo keng bai Li

Chorus

Bm A

祢是我心灵的满足

Li si goa sim leng e mua jiok

Bm A

祢是我唯一的喜乐

Li si goa wui yit e hee lok

Bm Em D Bm

在祢的脚前 我思想祢恩典

ti Li e ka zhyeng goa su siung Li wun dian

A Em D

我的神我要敬拜祢

goa e Sin goa beh keng pai Li"""

RAW['我们要靠主常常喜乐'] = r"""你们要靠主常常喜乐 (福)

E key | 150bpm | 4/4

Verse

E E

你们要靠主常常喜乐

lan lang beh ko Chu siong siong hee lok

E B E

要靠主常常喜乐

beh ko Chu siong siong hee lok

E E

你们要靠主常常喜乐

lan lang beh ko Chu siong siong hee lok

E B7 E

要靠主常常喜乐

beh ko Chu siong siong hee lok

Chorus

E E7 A B E

喜乐 喜乐 要靠主常常喜乐

hee lok hee lok beh ko Chu siong siong hee lok

E E7 F\#m B E

喜乐 喜乐 要靠主常常喜乐

hee lok hee lok beh ko Chu siong siong hee lok

神要我每天都高兴 (广)

D key | 150bpm | 4/4

Verse x 2

D A

神要我每天都高兴

San yiu ngo mui tin dou gou heng

D A D

个地苦恼不须理

go dei fu nou bat soi lei

Chorus x 2

D D A D

欢欣 欢欣 皆因主是我喜乐

fung yan fung yan gai yan Ju si ngo hei lok"""

RAW['我们带着赞美诗'] = r"""生命在於祢 G Em

我们带着赞美诗 (广)

C key | 135bpm | 4/4

Verse

C Dm C/E

我们来到主面前

ngo mun loi dou Ju min cin

F C

献上衷心的赞美

hin soeng zung sam dik zaan mei

C Dm C/E

我们来到主面前

ngo mun loi dou Ju min cin

F G C

献上衷心的赞美

hin soeng zung sam dik zaan mei

Chorus

F C

我们以感恩为祭

ngo mun yi gam yan wai zai

Dm C C7

因祢配得尊贵和荣耀

yan Nei pui dak jun gwai wo wing yiu

F C

我们以颂赞为祭

ngo mun yi zung zaan wai zai

Dm G C

因祢是万王之王

yan Nei si maan Wong zi Wong

我们带着赞美诗 (福)

C key | 135bpm | 4/4

Verse

C Dm C/E

我们带着赞美诗

lan lang thoa tio oh lo si

F C

进入耶和华圣殿

chin lip Ya-Ho-Hwa seng tiam

C Dm C/E

我们带着赞美诗

lan lang thoa tio oh lo si

F G C

进入耶和华圣殿

chin lip Ya-Ho-Hwa seng tiam

Chorus

F C

以感恩的心献祭

yi kam wun e sim hean khi

Dm C C7

献上赞美归耶和华

hean siong oh lo gui Ya-Ho-Hwa

F C

以感恩的心献祭

yi kam wun e sim hean khi

Dm G C

带着喜乐的心

thoa tio hee lok e sim"""

RAW['万物赞之声'] = r"""万物赞之声 (广)

C key | 70bpm | 4/4

Verse

C F

山击掌 水高唱 众星也和应

san gik zoeng soi gou coeng

zung sing ya wo ying

C G

风轻吹 吹起赞之声

fung hing coi coi hei zaan zi sing

C F

花摆腰 草偷笑 要兴奋做证

faa baai yiu cou tau siu

yiu heng fan zou zing

C G C

颂唱主基督已经得胜

zung coeng Ju Gei-Duk yi ging dak sing

Chorus

C F

永活耶稣 尊贵崇高

wing wut Ye-Sou jun gwai sung gou

G C G C

讴歌赞美祂至美至荣

au go zan mei Taa zi mei zi wing

C F

遍地同庆 普世同声

pin dei tung hing pou sai tung seng

G C

歌声句句动听

go sing goi goi dung ting"""

RAW['无限的爱'] = r"""生命在於祢 G Em

无限的爱 (福)

C key | 72bpm | 4/4

Verse

C Am Dm G

主祢是我的生命 风雨同心逗阵走

Chu Li si goa e si mia

hong ho tang sim tau tin khia

C Am Dm (G) G (C)

梦中有祢甲阮来作伴 脚步有祢的引导

bang tiong wu Li kap gun lai choe phoa

kha po wu Li e ing chhoa

Pre-chorus

Dm Am Dm D G

感谢祢对阮的爱 给我机会对头来

kam sia Li dui gun e ai ho goa ki hoe tui tau lai

C Am

天顶白云伴阮走天涯

thi teng peh hun phoa gun chau thin gai

Dm G C

天父永远甲我同在

Thi-Peh eng oan kap goa dang zai

Chorus

C Am F D G

我欲大声唱乎人知 耶和华有无限的爱

goa beh dua sia chiu ho lang zai

Ya-Ho-Hoa wu bo han e ai

C F Dm G C

世间的人拢来敬拜 耶和华是完全的爱

se kan e lang long lai keng bai

Ya-Ho-Hua si wan choan e ai"""

RAW['王小二拜年'] = r"""王小二过年 (广；新年歌)

E key | 110bpm | 4/4

Verse

E

一年过了一年主都带领

yat nin gwo liu yat nin Ju dou dai leng

心里欢喜笑咪咪庆祝新年

sam loi foon hei siu mei mei hing zuk san nin

C\#m E C\#m E

主是我的泉源 赐我恩典连连

Ju si ngo dik qun yun ci ngo yan din lin lin

E B E C\#m

要将福音传 赞美主恩惠

yiu zoeng fuk yam qun zan mei Ju yan wai

F\#m B B

主恩胜一切 呀依呀嘿

Ju yan saang yat cai ya yi ya hei

Chorus

E A E

赞美主 赞美主 赞美我救主

zan mei Ju zan mei Ju zan me ingo gau Ju

A E/G\# F\#m B

我与你手牵手 庆祝快乐年

ngo yu nei sau hin sau hing zuk fai lok nin

王小二过年 (福；新年歌)

E key | 110bpm | 4/4

Verse

E

一年过了一年主都带领

jit ni kway liao jit ni Chu long dua nia

心里欢喜笑咪咪庆祝新年

sim lai hua hee qio bi bi keng jiok sin ni

C\#m E C\#m E

主是我的泉源 赐我恩典连连

Chu si goa e chuan guan su goa wun dian lian lian

E B E C\#m

要将福音传 赞美主恩惠

beh jiong hok yim duan oh lo Chu wun hui

F\#m B B

主恩胜一切 呀依呀嘿

Chu wun seng yit ceh ya yi ya hei

Chorus x 2

E A E

赞美主 赞美主 赞美我救主

oh lo Chu oh lo Chu oh lo goa kiu Chu

A E/G\# F\#m (B) B (E)

我与你手牵手 庆祝快乐年

goa ka li qiu khan qiu keng jiok kuai lok ni"""

RAW['我要单单仰望祢'] = r"""我要单单仰望祢 (广)

D key | 67bpm | 4/4

Verse

D Em

我要单单仰望祢 主耶稣

ngo yiu dan dan yoeng mong Nei Ju Ye-Sou

A D

因为祢是我的帮助

yan wai Nei si ngo dik bong zo

D7 G Gm/Bb

我要单单仰望祢 主耶稣

ngo yiu dan dan yoeng mong Nei Ju Ye-Sou

A D

因为祢是我倚靠

yan wai Nei si ngo yi kau

Chorus

Em A D

我要仰望 仰望耶稣

ngo yiu yoeng mong yoeng mong Ye-Sou

D G/B Em A

我要仰望祢的荣美

ngo yiu yoeng mong Nei dik wing mei

Em A D A/C\# Bm

我要仰望 仰望耶稣

ngo yiu yoeng mong yoeng mong Ye-Sou

D/A A D

仰望耶稣的荣美

yoeng mong Ye-Sou dik wing mei

我要单单仰望祢 (福)

D key | 67bpm | 4/4

Verse

D Em

我要单单仰望祢 主耶稣

goa beh dan dan yong bong Li Chu Ya-So

A D

因为祢是我的帮助

yin wui Li si goa e pang cho

D7 G Gm/Bb

我要单单仰望祢 主耶稣

goa beh dan dan yong bong Li Chu Ya-So

A D

因为祢是我倚靠

yin wui Li si goa e woa ko

Chorus

Em A D

我要仰望 仰望耶稣

goa beh yong bong yong bong Ya-So

D G/B Em A

我要仰望祢的荣美

goa beh yong bong Li e eng bee

Em A D A/C\# Bm

我要仰望 仰望耶稣

goa beh yong bong yong bong Ya-So

D/A A D

仰望耶稣的荣美

yong bong Ya-So e eng bee"""

RAW['我要尽心尽性来敬拜我主'] = r"""我要尽心尽意来敬拜我主 (广)

Cm key | 125bpm | 4/4

Verse

Cm Fm

我要尽心尽意来敬拜我主

ngo yiu zeon sam zeon yi loi ging baai ngo Ju

Cm G

我要用诗歌来赞美祂

ngo yiu yung si go lai zaan mei Taa

Cm Fm

我要尽心尽性来敬拜我主

ngo yiu zeon sam zeon sing loi ging baai ngo Ju

Cm G7 Cm

我要天天赞美祂

ngo yiu tin tin zaan mei Taa

Chorus

Fm Cm

因我的神是伟大的神

yan ngo dik San si wai daai dik San

Fm G7 Cm

祂配受极大的赞美

Taa pui sau gik daai dik zaan mei

Fm Cm

因我的神是伟大的神

yan ngo dik San si wai daai dik San

Cm G7 Cm

我要尽力来赞美祂

ngo yiu zeon lik lai zaan mei Taa

我要尽心尽性来敬拜我主 (福)

Cm key | 125bpm | 4/4

Verse

Cm Fm

我要尽心尽性来敬拜我主

goa beh jin sim jin yi lai keng bai goa Chu

Cm G

我要用诗歌来赞美祂

goa beh eng si gwa lai oh lo Yi

Cm Fm

我要尽心尽性来敬拜我主

goa beh jin sim jin yi lai keng bai goa Chu

Cm G7 Cm

我要天天赞美祂

goa beh tian tian oh lo Yi

Chorus

|Fm |Cm

|Fm G7 |Cm

因我的神是伟大的神

yin goa e Sin si wui dua e Sin

祂配受极大的赞美

Yi pui siu gek dua e oh lo

因我的神是伟大的神

yin goa e Sin si wui dua e Sin

我要尽力来赞美祂

goa beh jin lat lai oh lo Yi"""

RAW['我要敬拜主耶稣直到永远'] = r"""Shekinah 荣耀 (G)

我要敬拜主耶稣直到永远 (福)

A key | 68bpm | 4/4

Verse

A F\#m

我要敬拜主耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

D E

我要敬拜主耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

D E/D

就算大风大浪一直攻击

iio seng dua hong dua eng yit tey gong keh

C\#m F\#m

在我生命中

ti goa xi mia tiong

Bm E A

我要敬主拜耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

Chorus

A F\#m

我的阿爸父 求祢保\~守我生命

goa e ah ba peh kiu Li po siu goa xi mia

D E

使我一生都配得 祢恩典

ho goa yit seng long pui tek Li wun dian

A F\#m

我的阿爸父 祢是我\~的牧者

goa e ah ba peh Li si goa e bok jia

D E A

使我一生跟随祢 永不回头

ho goa yit seng gun tueh Li eng bo huey tau

我要敬拜主耶稣直到永远 (福)

C key | 68bpm | 4/4

Verse

C Am

我要敬拜主耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

F G

我要敬拜主耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

F G/F

就算大风大浪一直攻击

iio seng dua hong dua eng yit tey gong keh

Em Am

在我生命中

ti goa xi mia tiong

Dm G C

我要敬主拜耶稣直到永远

goa beh keng bai Chu Ya-So dit kau eng goan

Chorus

C Am

我的阿爸父 求祢保\~守我生命

goa e ah ba peh kiu Li po siu goa xi mia

F G

使我一生都配得 祢恩典

ho goa yit seng long pui tek Li wun dian

C Am

我的阿爸父 祢是我\~的牧者

goa e ah ba peh Li si goa e bok jia

F G C

使一生跟随祢 永不回头

ho goa yit seng gun tueh Li eng bo huey tau"""

RAW['越唱越快活'] = r"""越唱越快活 (福)

E key | 142bpm | 4/4

Verse 1

|E |E |F\#m |F\#m

|B |B |E |E

有时有很多烦恼 心肝真辛苦

woo si woo cin zueh hoan lo

sim gua cin khang kho

有时有很多事情 我看不清楚

woo si woo cin zueh dai ji

goa kua beh cheng cho

|C\#m |C\#m |F\#m |F\#m

|B |B |F\#m B |E

有时有人讲东讲西 误会上 误会下

woo si woo lang kong tang kong sai

goh hui khi goh hui lo

遇到这么样的时间 第一好是来赞美

tu tio ah neh khuan e si kan

teh yit ho si lai oh lo

Chorus

|E |E |F\#m |F\#m

|B |B |E |E

来唱啦。。。唱哈利路亚

lai chio la… lai chio ha-li-lu-ya

来唱啦。。。给主耶稣听

lai chio la… ho Chu Ya-So thia

|C\#m |C\#m |F\#m |F\#m

|B |B |E |E

来唱啦。。。唱歌给主听

lai chio la… chio gua ho Chu thia

来唱啦。。。越唱越快活

lai chio la… na chio na khuah woah"""

RAW['有福气的人'] = r"""有福气的人 (福)

B key | 128bpm | 4/4

Verse

B G\#m F\# E F\#

耶稣疼咱世间人 祂将天理福气带给咱

Ya-So thia lan se kan lan

Yi chiong thi li hok khi toa ho lan

B G\#m D\#m E F\# B

牺牲生命来世间 将咱重担拢释放

hee seng si mia lai se kan

chiong lan tang ta long thau pang

C\#m C\#m/B C\#m F\# C\#m C\# F\#

因为祂的 大疼爱 赢过世间的苦难

yin ui Yi e toa thia thang

ya koe se kan e kho lan

B D\#m7 G\#m C\#m F\# B

你若伸手给祂牵 就有平安与盼望

li na chhun chhiu ho Yi khan

tio wu peng an ka ng bang

Chorus

B G\#m

信祂的就是有福气的人

xin Yi e tio si wu hok khi e lang

E B

这款机会岂可放

chit khoan ki hoe kiam tang pang

D\#m G\#m C\#m C\# F\#

事事项项有祂帮助 心内苦痛变轻松

su su hang hang wu Yi pang chan

sim lai thong khor pian khin sang

B G\#m

信祂的就是有福气的人

xin Yi e tio si wu hok khi e lang

E F\#

这款机会岂可放

chit khoan ki hoe mm tang pang

B G\#m E F\# B

欢欢喜喜在主内面 享受快乐一世人

hoa hoa hee hee ti Chu lai bin

hiong siu khoai lok chit se lang"""

RAW['耶稣进入我心'] = r"""耶稣进入我心 (福)

C key | 73bpm | 4/4

Verse 1

C F C

我的心事谁人知 眼泪滴滴留落来

goa e sim su sia lang zai bak sai tih tih lau loh lai

C G

我的心中充满了悲哀

goa e sim tiong qiong mua liau pi ai

F C Am

日夜流浪放荡 金银财宝我拢爱

jit mi liu long pang tang

kim yia cai poh goa long ai

Dm (G) G (C)

生活在黑暗的世界

seng wua zai oo am e se kai

Verse 2

现在听见主的呼唤 主的脚步响起来

hian tsai thia kin Chu e ho hoan

Chu e kha po hiang khi lai

主的赦免恩惠随来

Chu e sia bian wun hui sui lai

叫我悔改悔改 接受耶稣进心内

kio goa hue kai hue kai

jiap siu Ya-So jip sim lai

给主的光明照进来

jiong oo amm lai wui kong bing

Chorus

C F C

主耶稣耶稣 进入我心内

Chu Ya-So jin jip goa sim lai

C Dm G

你的爱常与我同在

Li e ai siong kah goa tang zai

C F C

主耶稣耶稣 进入我心内

Chu Ya-So jin jip goa sim lai

Dm G C

叫我明白主恩主的爱

Kio goa beng peh Chu wun Chu e ai"""

RAW['一生跟随祢'] = r"""一生跟随祢 (广)

C key | 146bpm | 4/4

Verse

C F C

一生仰望祢 一生跟随祢

yat saang yoeng mong Nei

yat saang gan ceoi Nei

F Em Am Dm G

奉献一生归给祢 何等福气

fung hin yat saang gwai kap Nei

ho dang fook hei

C F C

来到主面前 我心真欢喜

loi dou Ju min cin ngo sam zan foon hei

F Em Am Dm G C

奉献一生归给祢 一生跟随祢

fung hin yat saang kwai kap Nei

yat saang gan ceoi Nei

Chorus

F Em Dm C

大恩典真奇妙 何等奥秘

daai yan din zan kei miu ho dang ou bei

D D7 G D G

起初已选我何等的福气

hei co yi syun ngo ho dang dik fook hei

C F C

来到主面前 我心真欢喜

loi dou Ju min cin ngo sam zan foon hei

F Em Am Dm G C

奉献一生归给祢 一生跟随祢

fung hin yat saang kwai kap Nei

yat saang gan ceoi Nei

一生跟随祢 (福)

C key | 146bpm | 4/4

Verse

C F C

一生仰望祢 一生跟随祢

yit seng yong bong Li

yit seng gun tueh Li

F Em Am Dm G

奉献一生归给祢 何等福气

hong hean yit seng gui ho Li

ho teng hok khi

C F C

来到主面前 我心真欢喜

lai kau Chu bin zhyeng

goa sim jin hua hee

F Em Am Dm G C

奉献一生归给祢 一生跟随祢

hong hean yit seng gui ho Li

yit seng gun tueh Li

Chorus

F Em Dm C

大恩典真奇妙 何等奥秘

dua un dian jin ki biao ho teng au bi

D D7 G D G

起初已选我何等的福气

ki cho yi suan goa ho teng e hok khi

C F C

来到主面前 我心真欢喜

lai kau Chu bin zhyeng

goa sim jin hua hee

F Em Am Dm G C

奉献一生归给祢 一生跟随祢

hong hean yit seng gui ho Li

yit seng gun tueh Li"""

RAW['耶稣祢是宝贵'] = r"""耶稣祢是宝贵 (福)

D key | 68bpm | 4/4

Verse x 2

D Em A D Bm

耶稣祢是宝贵 祢对我真宝贵

Ya So Li si po gui Li tui goa chin po gui

Em A D

祢流宝血洗净我 祢爱使我自由

Li lao po hoeh soe cheng goa Li ai ho goa zu iu

Chorus

Em A

我只想天天来赞美祢

goa chi siung tian tian lai o lo Li

D A/C\# Bm

我只想要彰显祢的名

goa chi siung beh jiong hean Li e mia

Em A D

主啊我爱祢 我要更爱祢

Chu ah goa ai Li goa beh ko ai Li

Em A

我只想一生来事奉祢

goa chi siung yit seng lai su hong Li

D A/C\# Bm

我只想要荣耀祢的名

goa chi siung beh eng yao Li e mia

Em A D

主啊我爱祢 我要更爱祢

Chu ah goa ai Li goa beh ko ai Li

耶稣祢是宝贵 (广)

E key | 68bpm | 4/4

Verse x 2

E F\#m B E C\#m

耶稣祢是宝贵 祢对我真宝贵

Ye-Sou Nei si bou gwai Nei doi ngo zan bou gwai

F\#m B E

祢流宝血洗净我 祢爱使我自由

Nei lau bou hyut sai zeng ngo Nei oi sai ngo zi yau

Chorus

F\#m B

我只想天天来赞美祢

ngo zi soeng tin tin loi zaan mei Nei

E B/D\# C\#m

我只想要彰显祢的名

ngo zi soeng yiu zoeng hin Nei dik ming

F\#m B E

主啊我爱祢 我要更爱祢

Ju ah ngo oi Nei ngo yiu gang oi Nei

F\#m B

我只想一生来事奉祢

ngo zi soeng yat saang loi si fung Nei

E B/D\# C\#m

我只想要荣耀祢的名

ngo zi soeng yiu wing yiu Nei dik ming

F\#m B E

主啊我爱祢 我要更爱祢

Ju ah ngo oi Nei ngo yiu gang oi Nei"""

RAW['真欢喜我心有主耶稣'] = r"""夸胜 (D)

真欢喜因我心有主耶稣 (广)

D key | 143bpm | 4/4

Verse

|D |G |A7 |D

真欢喜我心有主耶稣

zan foon hei ngo sam yau Ju Ye So

真欢喜我心有主耶稣

真欢喜我心有主耶稣

哈利路亚 赞美主

ha lei lu ya zaan mei Ju

Chorus

|D |D7 |A7 |D

赞美主 阿门 赞美主 阿门

zaan mei Ju ah men

赞美主 阿门 赞美主 阿门

赞美主 阿门 赞美主 阿门

哈利路亚 赞美主

ha lei lu ya zaan mei Ju

真欢喜因我心有主耶稣 (福)

D key | 143bpm | 4/4

Verse

|D |G |A7 |D

真欢喜我心有主耶稣

jin hua hee gua sim wu Chu Ya-So

真欢喜我心有主耶稣

真欢喜我心有主耶稣

哈利路亚 赞美主

ha li lu ya oh lo Chu

Chorus

|D |D7 |A7 |D

赞美主 阿门 赞美主 阿门

oh lo Chu ah men

赞美主 阿门 赞美主 阿门

赞美主 阿门 赞美主 阿门

哈利路亚 赞美主

ha li lu ya oh lo Chu"""

RAW['在我心里有一首诗'] = r"""在我心里有一首诗 (广)

D key | 136bpm | 4/4

Verse

D A

在我心里有一首诗

zoi ngo sam lei yau yat sau si

A D

在我心里有一首诗

zoi ngo sam lei yau yat sau si

D D7 G

在我心里有一首诗

zoi ngo sam lei yau yat sau si

D A D

献给万王之王

hin kap maan wong zi wong

Chorus

D G A D

赞美敬拜祂 赞美敬拜祂

zaan mei ging bai Ta

D D7 G

在我心里有一首诗

zoi ngo sam lei yau yat sau si

D A D

献给万王之王

hin kap maan wong zi wong"""

RAW['主我敬拜祢'] = r"""主我敬拜祢 (广)

D key | 72bpm | 4/4

Verse

D A/C\# Bm D/A

主 我敬拜祢

Ju ngo ging bai Nei

G D/F\# Asus A

敞开在祢的 面前

cong hoi zoi Nei dik min cin

D A/C\# Bm D/A

主 我敬拜祢

Ju ngo ging bai Nei

Em A D

俯伏祢宝座前敬拜祢

fu fuk Nei bou zo cin ging bai Nei

Chorus

D A/C\# Bm D/A

天军向祢屈膝

tin gwan hoeng Nei wat sat

G Em7 A

众天使围绕祢座前

zung tin si wai yiu Nei zo cin

D A/C\# Bm D/A

主我双手举起

Ju ngo soeng Sau goi hei

Em7 A D

屈膝祢宝座前敬拜祢

wat sai Nei bou zo cin ging bai Nei"""

RAW['早晚都要赞美主'] = r"""早晚都要赞美主 (福)

A key | 128bpm | 4/4

Verse x 2

|A

早晨我要赞美

za ki goa beh oh lo

|A

夜晚我要赞美

mi si goa beh oh lo

|D E |A

早晚都要赞美主

za amm long beh oh lo Chu

Chorus

|D |D |E |E

赞美主 赞美主

oh lo Chu oh lo Chu

|D |D |E |E

赞美主 赞美主

|D E |A

早晚都要赞美主

za amm long beh oh lo Chu

早晚都要赞美主 (广)

A key | 128bpm | 4/4

Verse x 2

|A

早晨我要赞美

zou san ngo yiu zaan mei

|A

夜晚我要赞美

ye maan ngo yiu zaan mei

|D E |A

早晚都要赞美主

zou maan dou yiu zaan mei Ju

Chorus

|D |D |E |E

赞美主 赞美主

zaan mei Ju zaan mei Ju

|D |D |E |E

赞美主 赞美主

|D E |A

早晚都要赞美主

zou maan dou yiu zaan mei Ju"""

RAW['主有谁能与祢相比'] = r"""主有谁能与祢相比 (福)

D key | 66bpm | 4/4

Verse

D A

主有谁能与祢相比

Chu wu sia lang ka Li sia pi

G D

主有谁能比祢美丽

Chu wu sia lang pi Li bi lei

D A

主我要来敬拜祢

Chu goa beh lai keng bai Li

Em A D

因为祢是道路生命真理

yin wui Li si to lo jin li si mia

Chorus

D G

唱歌为要赞美祢

chio gwa wui tio oh lo Li

A D

只想颂扬祢的名

ji siung song yung Li e mia

D/F\# Bm

活着为要事奉祢

wah tioh wui tio su hong Li

Em A D

荣耀 全归祢圣名

eng yao zhuan gui Li seng mia

主有谁能与祢相比 (广)

D key | 66bpm | 4/4

Verse

D A

主有谁能与祢相比

Ju yau soi nang yu Nei soeng bei

G D

主有谁能比祢美丽

Ju yau soi nang bei Nei mei lai

D A

主我选择敬拜祢

Ju ngo xun zaak ging bai Nei

Em A D

因为祢是道路真理生命

yan wai Nei si dou lou zan lei sang meng

Chorus

D G

唱歌为要赞美祢

coeng go wai yiu zan mei Nei

A D

只想颂扬祢的名

zi soeng zung yoeng Nei dik meng

D/F\# Bm

活着为要事奉祢

wut zoek wai yiu si fung Nei

Em A D

荣耀 全归祢圣名

wing yiu qun gwai Nei sing meng"""

RAW['主愿我单属祢'] = r"""夸胜 (D)

主愿我单属祢 (福)

E key | 66bpm | 4/4

Verse

E A

我的主 我心爱祢

goa e Chu goa sim ai Li

E B

我的主 我渴慕祢

goa e Chu goa kek bo Li

E A

愿祢爱来吸引我

goan Li ai lai kip yin goa

E/B B E

使我心 单单爱祢

ho goa sim dan dan ai Li

Chorus

E B

哦耶稣 我需要祢

oh Ya-So goa su yao Li

A E

炼净我 完全属祢

lian zyeng goa wan zuan siok Li

C\#m F\#m

愿祢爱 来摸着我

goan Li ai lai mo tio goa

A B E

使我心 全然属祢

ho goa sim zuan lian siok Li

主愿我单属祢 (广)

D key | 66bpm | 4/4

Verse

D G D A

我的主 我心爱祢 我的主 我渴慕祢

ngo dik Ju ngo sam oi Nei

ngo dik Ju ngo hot mou Nei

D G D/A A D

愿祢爱来吸引我 使我心 单单爱祢

yun Nei oi loi kap yan ngo

sai ngo sam dan dan oi Nei

Chorus

D A G D

哦耶稣我需要祢 炼净我完全属祢

Oh Ye-Sou ngo seoi yiu Nei

lin zing ngo yun qun suk Nei

Bm Em G A D

愿祢爱来摸着我 使我心 全然属祢

yun Nei oi loi mo zoek ngo

sai ngo sam qun yun suk Nei"""

RAW['主耶稣知我心'] = r"""主耶稣知我心 (福)

D key | 73bpm | 4/4

Verse

D Bm Em G

主耶稣知我心 安慰我给我生命

Chu Ya-So zai goa sim

an wui goa ho goa xi mia

D Bm G A

赐我平安赐我喜乐 走过风雨路

su goa peng an su goa hee lok

gia koe hong ho loh

D F\#m G E/G\#

祂会明白 祂拢了解

Yi eh beng peh\~ Yi long liao gai

Em D/F\# Em A D

抹去我的眼泪 给我真实在

qik ki goa e bak sai ho goa jin sit zai

Chorus

G D

搖呀 摇呀 风雨吹不倒

yo ah yo ah hong ho chuey buey toh

G Em A

牵我 疼我 永远会照顾

kan goa tia goa eng guan eh jiao ko

D Bm Em G

也是我的信心 是我的帮助

Yi si goa e sin sim si goa e pang zo

D Bm Em A D

坚强我的心灵 耶稣真真好

keng kiong goa e sim leng

Ya-So jin jin ho"""

RAW['在主爱里'] = r"""在主爱里 (福)

D key | 146bpm | 4/4

Verse

D G

我敬拜祢因祢先爱我

goa keng bai Li yin li sin ai goa

A D

主我敬拜祢

Chu goa keng bai Li

D G

我时常敬拜主我神

goa si siung keng bai Chu goa Sin

A D

主我敬拜祢

Chu goa keng bai Li

Chorus x 2

D D7 G A D

主爱 主爱 我惦在主的爱

Chu ai Chu ai goa diam teh Chu e ai

在主爱里 (广)

D key | 146bpm | 4/4

Verse

D G

我敬拜祢因祢先爱我

ngo ging baai Nei yan Nei sin oi ngo

A D

主我敬拜祢

Ju ngo ging baai Nei

D G

我时常敬拜主我神

ngo si soeng ging baai Ju ngo San

A D

主我敬拜祢

Ju ngo ging baai Nei

Chorus x 2

D D7 G A D

主爱 主爱 与主同在爱里

Ju oi Ju oi yu Ju tung zoi oi leoi"""

RAW['坐在宝座上圣洁羔羊'] = r"""坐在宝座上圣洁羔羊 (福)

G key | 74bpm | 4/4

Verse 1

G D/F\# Em C D Bm

坐在宝座上圣洁羔羊 我们跪落敬拜祢

ze di bo zo siong sing keat go yiung

lan lang gui lok k1eng bai Li

C D Bm Em

昔在今在以后永在

sek zai kim zai yi ao eng zai

Am Am/G F D

唯有祢是全能真神

wui wu Li is chuan leng jin Sin

Verse 2

G D/F\# Em C D Bm

坐在宝座上尊贵羔羊 我们跪落敬拜祢

ze di bo zo siong zun gui go yiung

lan lang gui lok k1eng bai Li

C D Bm Em

颂赞尊贵荣耀权势

song zan zun gui eng yao kuan sek

C G/B Am7 D

都归给祢直到永远

long gui ho Li dit kao eng wan

Chorus

G Em

万王之王 万主之主

ban ong ji Ong ban chu ji Chu

C D G

唯有祢配得敬拜和尊崇

wui wu Li pui tek keng bai ka zun qiong

G Em

万王之王 万主之主

ban ong ji Ong ban chu ji Chu

C D G

我们高举祢圣名直到永远

lan lang go gu Li seng mia dit kao eng wan

坐在宝座上圣洁羔羊 (广)

G key | 74bpm | 4/4

Verse 1

G D/F\# Em C D Bm

坐在宝座上圣洁羔羊 我们俯伏敬拜祢

co zoi bou zo soeng seng git Gou Yoeng

ngo mun fu fook ging baai Nei

C D Bm Em

昔在今在以后永在

sik zoi gam zoi yi hau wing zoi

Am Am/G F D

唯有祢是全能真神

wai yau Nei si qun nang zan San

Verse 2

G D/F\# Em C D Bm

坐在宝座上尊贵羔羊 我们俯伏敬拜祢

co zoi bou zo soeng seng git Gou Yoeng

ngo mun fu fook ging baai Nei

C D Bm Em

颂赞尊贵荣耀权势

zung zaan jun gwai wing yiu kyun sai

C G/B Am7 D

都归给祢直到永远

dou gwai kap Nei zik dou wing yun

Chorus

|G |Em

|C D |G

万王之王 万主之主

maan Wong zi Wong maan Ju zi Ju

唯有祢配得敬拜和尊崇

wai yau Nei pui dak ging baai wo jun sung

万王之王 万主之主

maan Wong zi Wong maan Ju zi Ju

我们高举祢圣名直到永远

ngo mun gou geoi Nei seng meng zik dou wing yun"""

RAW['真正好'] = r"""真正好/主耶稣真好 (福)

D key | 145bpm | 4/4

Verse

D G D

真正好 来信耶稣真正好

jin jia ho lai sin Ya-So jin jia ho

D Em A

真正好 来信耶稣真正好

jin jia ho lai sin Ya-So jin jia ho

D D7 G

我拜一拜二拜三拜四拜五拜六

goa pai yit pai ji pai sa pai si pai go pai lak

G7 D Em A D

整个礼拜真正好 来信耶稣真正好

kui e leh pai jin jia ho lai sin Ya-So jin jia ho

Chorus

D F\#m

主耶稣真好 我要来赞美

Chu Ya-So jin ho goa beh lai oh lo

G A

我的耶稣对我真好

goa e Ya-So tui goa jin ho

D F\#m

拿掉我的烦恼 使我每日笑

gia tiau goa e hoan lo ho goa tak jit chhio

G A D

我的耶稣 对我真好

goa e Ya-So tui goa jin ho

真正好/主耶稣真好 (广)

D key | 145bpm | 4/4

Verse

D G D

真正好 来信耶稣真正好

ying zan hou loi seon Ye-Sou ying zan hou

D Em A

真正好 来信耶稣真正好

ying zan hou loi seon Ye-Sou ying zan hou

D D7 G

我拜一拜二拜三拜四拜五拜六

ngo baai yat baai yi baai saam

baai sei baai ng baai luk

G7 D Em A D

整个礼拜真正好 来信耶稣真正好

zing go lai baai ying zan hou

lai seon Ye-Sou ying zan hou

Chorus

D F\#m

主耶稣真好 我要来赞美

Ju Ye-Sou zan hou ngo yiu loi zaan mei

G A

我的耶稣对我真好

ngo dik Ye-Sou deoi ngo zan hou

D F\#m

拿掉我的烦恼 使我每日笑

naa diu ngo dik faan nou sai ngo mui yat siu

G A D

我的耶稣 对我真好

ngo dik Ye-Sou deoi ngo zan hou"""


# ── Inject into songs.json ───────────────────────────────────────────────────

def main():
    songs = json.loads(SONGS_PATH.read_text(encoding='utf-8'))

    # Index ALL songs (not just dialect) — some dialect versions live on non-dialect songs
    all_index: dict[str, dict] = {norm(s['title']): s for s in songs}

    updated, skipped, not_found = [], [], []

    for raw_title, raw_content in RAW.items():
        n = norm(raw_title)
        target = all_index.get(n)

        if not target:
            # Partial match: only accept if the shorter key is at least 4 chars
            # to avoid false positives on short generic titles like "赞美"
            candidates = [
                k for k in all_index
                if len(min(n, k, key=len)) >= 4 and (n in k or k in n)
            ]
            if candidates:
                target = all_index[candidates[0]]

        if not target:
            not_found.append(raw_title)
            continue

        lyrics = extract_with_romanization(raw_content)
        if not lyrics:
            not_found.append(f"{raw_title} -> empty extraction")
            continue

        if DRY_RUN:
            sys.stdout.buffer.write(
                f"\n{'='*60}\nID {target['id']} - {target['title']}\n{'='*60}\n{lyrics}\n".encode('utf-8')
            )
            updated.append(f"{target['id']} {target['title']}")
            continue

        target['lyrics'] = lyrics
        updated.append(f"{target['id']} {target['title']}")

    if not DRY_RUN:
        SONGS_PATH.write_text(
            json.dumps(songs, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    sys.stderr.reconfigure(encoding='utf-8')
    mode = '[DRY RUN] ' if DRY_RUN else ''
    sys.stderr.write(f'\n{mode}Updated {len(updated)} songs:\n')
    for s in updated:
        sys.stderr.write(f'  {s}\n')
    if skipped:
        sys.stderr.write(f'\nSkipped {len(skipped)}:\n')
        for s in skipped:
            sys.stderr.write(f'  {s}\n')
    if not_found:
        sys.stderr.write(f'\nNot found ({len(not_found)}):\n')
        for s in not_found:
            sys.stderr.write(f'  {s}\n')

if __name__ == '__main__':
    main()
