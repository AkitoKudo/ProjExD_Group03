import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/3.png"), 0, 1.5)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        simg0 = pg.transform.rotozoom(pg.image.load(f"fig/0.png"), 0, 1.5)
        simg = pg.transform.flip(simg0, True, False)
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.simgs = {
            (0,0):simg,
            (+1, 0): simg,  # 右
            (+1, -1): simg,  # 右上
            (0, -1): simg,  # 上
            (-1, -1): simg0,  # 左上
            (-1, 0): simg0,  # 左
            (-1, +1): simg0,  # 左下
            (0, +1): simg0,  # 下
            (+1, +1): simg,  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.simage = self.simgs[self.dire]
        self.srect = self.simage.get_rect()
        self.srect.center = self.rect.center
        self.speed = 10
        self.mode = 0

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.5)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.mode == 1:
            self.image = self.simgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird,tscore):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        if tscore <= 50 :  # スコアの合計が50点以下
            rad = random.randint(10, 10)  # 爆弾円の半径：10の乱数
            self.speed = 2  # 爆弾の投下速度2
        elif 51 <= tscore <= 100 :  # スコアの合計が51点以上100点以下
            rad = random.randint(10, 20)  # 爆弾円の半径：10以上20以下の乱数
            self.speed = 3  # 爆弾の投下速度3
        elif 101 <= tscore <= 150:  # スコアの合計が101点以上150点以下
            rad = random.randint(10, 30)  # 爆弾円の半径：10以上30以下の乱数
            self.speed = 4  # 爆弾の投下速度4
        elif 151 <= tscore <= 200:  # スコアの合計が151点以上200点以下
            rad = random.randint(10, 40)  # 爆弾円の半径：10以上40以下の乱数
            self.speed = 5  # 爆弾の投下速度5
        elif 201 <= tscore:  # スコアの合計が201点以上250点以下
            rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
            self.speed = 6  # 爆弾の投下速度6
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0=0, mode=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle+=angle0
        if mode == 0:
            self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        elif mode == 1:
            self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 15
        self.count = 0

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.count += 1
            if self.count == 15:
                self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH,random.randint(0, HEIGHT)
        self.vx, self.vy = -6, 0
        self.bound = random.randint(WIDTH//2, WIDTH-50)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centerx < self.bound:
            self.vx = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

class EnemyBoss(pg.sprite.Sprite):
    """
    bossをつかさどるかんすう
    """
    def __init__(self, life:int):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/boss.png"), 0, 2.0)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH,(HEIGHT/2)
        self.vx, self.vy = -6, 0
        self.bound = WIDTH - 60  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(25, 100)
        self.life = life
    
    def update(self):
        """
        bossを速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateをstepに変更する
        引数 screen：画面Surface
        """
        if self.rect.centerx < self.bound and self.state == "down":
            self.vy = 6
            self.state = "step" #左右に移動する状態
            self.vx = 0
        if self.state == "step" and check_bound(self.rect) != (True,True):
            self.vy *= -1 #画面端についたら移動方向反転
        if self.interval != 0: #bombの発射レート制御
            self.interval -= 1
        elif self.interval == 0:
            self.interval = random.randint(25, 100)

        self.rect.move_ip(self.vx, self.vy)    

class NeoBeam(pg.sprite.Sprite):
    
    def __init__(self,bird:Bird,num):
        super().__init__()
        self.bird=bird
        self.num=num

    def gen_beams(self):
        return [Beam(self.bird,angle0,1)for angle0 in range(-12,+13,25//(self.num-1))]


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (250, 20, 20)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Bullet(pg.sprite.Sprite):
    """
    残弾数を表示するクラス
    """
    def __init__(self,bullet :pg.Surface,step=1,value=1,mvalue=1,mct=0,ns=0):
        self.font = pg.font.Font(None, 60)
        self.color = (10, 10, 10)
        self.mct = mct
        self.ct = 0
        self.step = step
        self.ns = ns
        self.mode = 0

        self.value = value
        self.mvalue = mvalue
        self.bimg = bullet
        self.back = pg.Surface((240,60))
        pg.draw.rect(self.back,(192,192,192), (0,0,140,60))
        pg.draw.rect(self.back,(100,255,100), (140,0,240,60))
        self.back.set_alpha(128)
        self.image = self.font.render(f"{self.value}", 0, self.color)
        self.brct = self.bimg.get_rect()
        self.bact = self.back.get_rect()
        self.rect = self.image.get_rect()
        self.brct.center = WIDTH-174, HEIGHT-(60*step) + 30
        self.bact.center = WIDTH-120, HEIGHT-(60*step) + 30
        self.rect.center = WIDTH-75, HEIGHT-(60*step) + 30

    def update(self,screen: pg.Surface,score):
        if self.value == 0:
            self.color = (255, 10, 10)
            if self.ct > 0:
                self.ct -= 1
        else:
            self.color = (10, 10, 10)
        if self.ct == 0 and self.ns <= score:
            self.value = self.mvalue
        if self.mode == 1:
            self.value -= 1
            if self.value == 0:
                self.mode = 0
        self.image = self.font.render(f"{self.value}", 0, self.color)
        screen.blit(self.back,self.bact)
        screen.blit(self.bimg,self.brct)
        screen.blit(self.image,self.rect)

class Life(pg.sprite.Sprite):
    """
    残機表示
    """
    def __init__(self,step=0):
        super().__init__()
        img=pg.transform.rotozoom(pg.image.load(f"fig/bh.png"),0,0.5)
        self.image=img
        self.rect=self.image.get_rect()
        if step==0:
            self.rect.center= 50,HEIGHT-100
        elif step==1:
            self.rect.center=100,HEIGHT-100
        elif step==2:
            self.rect.center=150,HEIGHT-100
        

    def update(self,screen:pg.surface):
        screen.blit(self.image,self.rect)
        



class Shield(pg.sprite.Sprite):
    """
    敵の攻撃を防ぐシールドを展開する
    """
    def __init__(self, bird: Bird ,life:int):
        """
        シールドの基本情報
        """
        super().__init__()
        bird.mode = 1
        self.vx ,self.vy = bird.dire 
        img = pg.Surface((bird.rect.height*1.8,bird.rect.height*1.8))
        pg.draw.circle(img,(50,255,50),(bird.rect.height*0.9,bird.rect.height*0.9),bird.rect.height*0.9)
        self.image = img
        self.image.set_alpha(100)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery
        self.rect.centerx = bird.rect.centerx
        self.life = life

    def update(self ,bird: Bird ,key_lst: list[bool]):
        """
        shieldをこうかとんの位置に基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.center = bird.rect.center
        self.life -= 1
        if self.life == 0:
            bird.mode = 0
            self.kill()


class Gravity(pg.sprite.Sprite):
    """
    重力場を発生させるクラス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.life = 400
        pg.draw.rect(self.image,(100,255,100), (0,0,WIDTH,HEIGHT))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH//2, HEIGHT//2 

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class Item(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        original_image = pg.image.load("fig/item.png")
        # 画像を元のサイズの40%に縮小
        scaled_size = (int(original_image.get_width() * 0.4), int(original_image.get_height() * 0.3))
        self.image = pg.transform.scale(original_image, scaled_size)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx = -6
        self.vy = 0
    
    def update(self):
        self.rect.move_ip(self.vx, self.vy)
        if 0 > self.rect.centerx:
            self.kill()

class Ball(pg.sprite.Sprite):
    """
    障害物（鉄球）に関するクラス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.image.load(f"fig/toge4.png") # 鉄球画像
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH,random.randint(0,HEIGHT)
        self.vx = -3
        self.vy = 0
        self.speed = 2

    def update(self):
        """
        鉄球を速度ベクトルself.vxとself.vyに基づいて移動させる
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if 0 > self.rect.centerx:
            self.kill()




def clear(screen,bg_img):
    screen.blit(bg_img, [0, 0])
    img = pg.image.load(f"fig/6.png")
    rct = img.get_rect()
    rct.center = WIDTH/3,HEIGHT/2
    screen.blit(img,rct)
    rct.centerx = WIDTH/3*2
    screen.blit(img,rct)
    font = pg.font.SysFont(None, 60)
    txt = font.render("GAME CLEAR", True, (255, 20, 20))
    txtxy = txt.get_rect()
    txtxy.center = WIDTH/2,HEIGHT/2
    screen.blit(txt,txtxy)


def main():
    pg.display.set_caption("極・こうかとんシューティング")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    bg_img_m = pg.transform.flip(bg_img,True,False)
    score = Score()
    zanki=Life()
    z_count=3
    tscore = 0

    bu_beam = Bullet(pg.transform.rotozoom(pg.image.load(f"fig/beam.png"),0,0.5),4,5,5,100,0)
    bu_unig = Bullet(pg.transform.rotozoom(pg.image.load(f"fig/beam.png"),0,0.5),3,1,1,200,0)
    bu_psyc = Bullet(pg.transform.rotozoom(pg.image.load(f"fig/0.png"),0,1),2,0,400,800,50)
    bu_grav = Bullet(pg.transform.rotozoom(pg.image.load(f"fig/6.png"),0,1),1,0,400,1200,200)

    bh_1=Life(0)
    bh_2=Life(1)
    bh_3=Life(2)

    bird = Bird(3, (550, 600))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()
    gravitys = pg.sprite.Group()
    balls = pg.sprite.Group()
    boss = pg.sprite.Group()
    bullets = [bu_beam,bu_unig,bu_psyc,bu_grav]
    lifes=[bh_1,bh_2,bh_3]
    

    tmr = 0
    clock = pg.time.Clock()

    items = pg.sprite.Group()
    item_timer = 0

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_c and len(shields) == 0 and score.value >= 50:
                if bu_psyc.ct <= 0:
                    shields.add(Shield(bird,400))
                    bu_psyc.mode = 1
                    bu_psyc.ct = bu_psyc.mct
                    score.value -= 50
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if key_lst[pg.K_LSHIFT]:
                    if bu_unig.ct <= 0:
                        m_beam = NeoBeam(bird, 3)
                        beams.add(m_beam.gen_beams())
                        bu_unig.value -= 1
                        bu_unig.ct = bu_unig.mct
                else:
                    if -5 < bu_beam.ct <= 0:
                        beams.add(Beam(bird))
                        bu_beam.value -= 1
                        bu_beam.ct -= 1
                    if bu_beam.ct <= (-5):
                        bu_beam.ct = bu_beam.mct
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and len(gravitys) == 0 and score.value >= 200:
                if bu_grav.ct <= 0:
                    gravitys.add(Gravity())
                    bird.change_img(6, screen)
                    bu_grav.mode = 1
                    bu_grav.ct = bu_grav.mct
                    score.value -= 200
        bg_x = tmr % 3200
        screen.blit(bg_img, [-bg_x, 0])
        screen.blit(bg_img_m,[-bg_x+1600,0])
        screen.blit(bg_img, [-bg_x+3200, 0])
        screen.blit(bg_img_m,[-bg_x+4800,0])

        if tmr%25 == 0 and len(boss) == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())
        elif tmr%100 == 0 and len(boss) == 1:
            emys.add(Enemy())
            emys.add(Enemy())
        
        item_timer += 1
        if item_timer >= 250:  # 50 FPS × 5 秒 = 250フレーム
            items.add(Item())
            item_timer = 0
 
        if tmr%100 == 0:  # 100フレームに1回、鉄球を出現させる
            balls.add(Ball())

        if score.value >= 1000 and len(boss) == 0:
            boss.add(EnemyBoss(10))

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird,score.value))

        for bos in boss:
            if bos.state == "step" and bos.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(bos, bird,score.value))

        for emy in pg.sprite.groupcollide(emys, beams, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            tscore += 10  # 10点加算
            
        for bos in pg.sprite.groupcollide(boss, beams, False, True).keys():
            bos.life -= 1
            exps.add(Explosion(bos, 10))
            if bos.life == 0:
                exps.add(Explosion(bos, 100))
                bos.kill()
                score.value += 10000000
                bird.change_img(6, screen) # こうかとん悲しみエフェクト
                boss.update()
                boss.draw(screen)
                exps.update()
                exps.draw(screen)
                score.update(screen)
                pg.display.update()
                time.sleep(1)
                clear(screen,bg_img)
                pg.display.update()
                time.sleep(2)
                return


        if bird.mode == 1 and score.value >= 1000:
            for emy in pg.sprite.groupcollide(emys, shields, True, False).keys():
                exps.add(Explosion(emy, 100))

        for bomb in pg.sprite.groupcollide(bombs, beams, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
            tscore += 1  # 1点加算

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for bomb in pg.sprite.groupcollide(balls, shields, True, False).keys(): # 鉄球がバリアに当たると爆発して無効化する
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト


        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            z_count-=1 # 残機を減らす
            if z_count ==0:
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            else:
                shields.add(Shield(bird,400)) # 被弾した際、残機が残ってる場合シールド獲得
                lifes.pop()
        
        if len(pg.sprite.spritecollide(bird, balls, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        

        
        for emy in pg.sprite.groupcollide(emys, gravitys, True, False).keys(): # 敵との衝突判定
            exps.add(Explosion(emy, 50))  # 爆発エフェクト
            
        for bomb in pg.sprite.groupcollide(bombs, gravitys, True, False).keys(): # 爆弾との衝突判定
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for item in pg.sprite.spritecollide(bird, items, True):
            bu_beam.ct = 0
            bu_unig.ct = 0

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        boss.update()
        boss.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        shields.update(bird,key_lst)
        shields.draw(screen)
        items.update()
        items.draw(screen)
        balls.update()
        balls.draw(screen)
        gravitys.update()
        gravitys.draw(screen)
        for i in lifes:
            i.update(screen)
        for i in bullets:
            i.update(screen,score.value)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()