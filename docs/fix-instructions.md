# 認可・挙動バグ修正指示

> 全APIエンドポイントの認可監査に基づく修正タスク
> 作成日: 2026-02-07

---

## 修正1 [HIGH]: ルームクローズの認可制御

### 現状の問題
`apps/api/app/routers/rooms.py` L153-177

`POST /api/rooms/{room_id}/close` はルームメンバーであれば誰でも即座にクローズできる。
悪意あるユーザーがマッチ成立直後にクローズすれば、相手は集合調整もチャットもできない。

### 修正方針
**双方合意クローズ**を実装する。

1. `RoomMember` モデルに `ready_to_close: bool = False` カラムを追加
2. `POST /api/rooms/{room_id}/close` を「自分の ready_to_close を True にする」操作に変更
3. 両メンバーが `ready_to_close = True` になった時点でルームを `closed` にする
4. 片方だけが押した場合は「相手の同意を待っています」状態を返す
5. WebSocket で相手に「クローズリクエストが来た」ことを通知する

### 必要な変更ファイル
- `apps/api/app/models/room.py` — `RoomMember` に `ready_to_close` カラム追加
- `apps/api/app/routers/rooms.py` — close エンドポイントのロジック変更
- `apps/api/alembic/versions/` — マイグレーション追加
- `apps/web/src/views/RoomView.vue` — UIに「クローズ待ち」状態を表示
- `apps/api/tests/` — 片方クローズ→未クローズ、双方クローズ→クローズのテスト

### API仕様変更
```
POST /api/rooms/{room_id}/close

レスポンス（片方のみ）:
  200 {"detail": "Waiting for other member to close", "status": "pending_close"}

レスポンス（双方完了）:
  200 {"detail": "Room closed", "status": "closed"}

レスポンス（既にclose済み）:
  400 {"detail": "You already requested close"}
```

---

## 修正2 [HIGH]: 通報エンドポイントのバリデーション強化

### 現状の問題
`apps/api/app/routers/reports.py` L16-39

- `reported_id` のユーザー存在チェックなし → 架空IDで通報スパム可能
- `room_id` のルーム存在チェックなし → 架空ルームIDを紐付け可能
- 通報者がそのルームのメンバーだったか未検証 → 無関係なルームの通報を偽装可能

### 修正内容
```python
# 1. reported_id のユーザー存在チェック
reported_user = await db.get(User, body.reported_id)
if not reported_user:
    raise HTTPException(status_code=404, detail="Reported user not found")

# 2. room_id が指定された場合のルーム存在チェック
if body.room_id:
    room = await db.get(Room, body.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 3. 通報者がそのルームのメンバーだったか検証
    membership = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == body.room_id,
            RoomMember.user_id == user.id,
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this room")
```

### 必要な変更ファイル
- `apps/api/app/routers/reports.py` — バリデーション追加
- `apps/api/tests/` — 存在しないID・無関係ルームでの通報が403/404になるテスト

---

## 修正3 [MEDIUM]: ブロックの対象ユーザー存在チェック

### 現状の問題
`apps/api/app/routers/blocks.py` L25-44

`blocked_id` のユーザーがDBに存在するか検証していない。存在しないUUIDをブロックできてしまう。

### 修正内容
```python
# create_block 内、重複チェックの前に追加
blocked_user = await db.get(User, body.blocked_id)
if not blocked_user:
    raise HTTPException(status_code=404, detail="User not found")
```

### 必要な変更ファイル
- `apps/api/app/routers/blocks.py` — 存在チェック追加
- `apps/api/tests/` — 存在しないIDブロックが404になるテスト

---

## 修正4 [MEDIUM]: ルームクローズのレート制限追加

### 現状の問題
`apps/api/app/routers/rooms.py` L153

`POST /api/rooms/{room_id}/close` にレート制限がない。

### 修正内容
```python
@router.post("/{room_id}/close")
@limiter.limit("5/minute")  # 追加
async def close_room(
    request: Request,  # limiter用に追加
    ...
```

### 必要な変更ファイル
- `apps/api/app/routers/rooms.py` — `@limiter.limit` デコレータ追加

---

## 修正5 [LOW]: 募集一覧でブロック済みユーザーの募集を非表示

### 現状の問題
`apps/api/app/routers/recruitments.py` L32-50

`GET /api/recruitments` は認証不要。ログインユーザーがブロックした相手の募集もそのまま表示される。マッチ成立時にブロックチェックがあるため実害は小さいが、ブロックした相手が一覧に出るのはUXが悪い。

### 修正方針
- 認証はOptionalにする（未ログインでも一覧は見られる）
- ログイン中ユーザーがいる場合、そのユーザーがブロックしている/されているユーザーの募集を除外する

### 修正内容
```python
from app.dependencies import get_optional_user  # 新しい依存関数

@router.get("", response_model=list[RecruitmentResponse])
async def list_recruitments(
    user: User | None = Depends(get_optional_user),  # Optional認証
    db: AsyncSession = Depends(get_db),
) -> list[RecruitmentResponse]:
    now = utcnow()
    stmt = (
        select(Recruitment, User.nickname)
        .join(User, User.id == Recruitment.user_id)
        .where(Recruitment.status == RecruitmentStatus.open, Recruitment.expires_at > now)
        .order_by(Recruitment.created_at.asc())
    )

    # ブロック関係にあるユーザーの募集を除外
    if user:
        blocked_ids_stmt = select(Block.blocked_id).where(Block.blocker_id == user.id)
        blocker_ids_stmt = select(Block.blocker_id).where(Block.blocked_id == user.id)
        stmt = stmt.where(
            Recruitment.user_id.not_in(blocked_ids_stmt),
            Recruitment.user_id.not_in(blocker_ids_stmt),
        )

    result = await db.execute(stmt)
    ...
```

### 必要な変更ファイル
- `apps/api/app/dependencies.py` — `get_optional_user` 関数を追加（Cookie無しでも None を返す）
- `apps/api/app/routers/recruitments.py` — 一覧クエリにブロック除外条件を追加
- `apps/api/tests/` — ブロック済みユーザーの募集が非表示になるテスト

---

## 実装順序

```
1. 修正2（通報バリデーション）  ← 最も簡単かつ影響大
2. 修正3（ブロック存在チェック） ← 1行追加
3. 修正4（クローズのレート制限） ← 1行追加
4. 修正1（双方合意クローズ）    ← DB変更あり、最も工数が大きい
5. 修正5（募集一覧ブロック除外） ← Optional認証の新パターン導入
```

## テスト方針
各修正に対して最低1つのユニットテストを追加すること:
- 修正1: 片方closeで未クローズ / 双方closeでクローズ / 2回closeで400
- 修正2: 架空reported_idで404 / 架空room_idで404 / 無関係ルームで403
- 修正3: 架空blocked_idで404
- 修正4: （レート制限のためテスト不要、既存パターンに準拠）
- 修正5: ブロック済みユーザーの募集が一覧に出ないこと
