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
