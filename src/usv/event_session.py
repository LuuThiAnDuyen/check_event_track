"""Chuan bi va don phien ghi - hai viec phai lam TRUOC khi ghi.

Tach khoi routes_event vi ca hai deu la LUAT, khong phai chuyen HTTP: mot cai
tra loi "co duoc ghi app nay khong", cai kia "phien truoc con gi phai don".
Route chi con viec goi va doi ma loi ra HTTP.
"""

from __future__ import annotations

from difflib import get_close_matches


from .adb_parsers import AdbError


async def lay_mau_app(adb, recording, *, ten_co_tren_may: bool = True) -> None:
    """Ghi lai app duoi test co dang chay khong, va app nao dang o foreground.

    Goi ca luc bat dau ghi va luc dung. Da thay chay mot lan la du - app co
    the bi dong truoc khi tester bam Dung.

    `foreground` chi ghi khi KHONG thay app duoi test chay: luc do bao cao phai
    chi ra app NAO dang mo, khong thi tester chi biet "khong ket luan duoc" ma
    khong biet phai sua gi. Da gap that: sai mot dau cham trong ten package.

    Loi adb o day KHONG duoc lam sap phien ghi - coi nhu chua thay la du an toan.
    """
    if not recording.checked_package:
        recording.checked_package = recording.package
    if recording.app_seen:
        return
    try:
        recording.app_seen = await adb.app_running(
            recording.serial, recording.checked_package)
    except AdbError:
        recording.app_seen = False
    if recording.app_seen:
        return

    try:
        recording.foreground = await adb.foreground_package(recording.serial) or ""
    except AdbError:
        recording.foreground = ""

    # Ten dan KHONG co tren may -> tester tu mo app, va tool khong co cach nao
    # biet ten dung ngoai viec xem app nao da o foreground trong phien.
    #
    # Chi lam khi ten dan khong ton tai. Ten dan CO tren may ma app khong chay
    # thi co gi sai that (app crash, mo khong len), va am tham doi sang app
    # dang mo la bao cao ve mot app tester khong he chon.
    if ten_co_tren_may:
        return
    doan = doan_app(recording)
    if not doan:
        return
    recording.checked_package = doan
    try:
        recording.app_seen = await adb.app_running(recording.serial, doan)
    except AdbError:
        recording.app_seen = False


def doan_app(recording) -> str:
    """App duoi test, doan tu so lan xuat hien o foreground trong ca phien.

    Lay app xuat hien NHIEU NHAT chu khong lay mau luc Dung ghi: lay mot mau
    thi cai gi dang tren man luc do thang - da do duoc, no bat ra launcher va
    bao cao ghi "da cham cho launcher".

    Loai launcher (lay chinh xac bang resolve-activity, khong doan theo ten) va
    system UI: chung luon xuat hien khi tester chuyen man, ma khong bao gio la
    app duoi test.
    """
    bo = {recording.home_package, "com.android.systemui", ""}
    dem = {ten: so for ten, so in recording.foreground_seen.items()
           if ten not in bo}
    if not dem:
        return ""
    return max(dem, key=lambda ten: (dem[ten], ten))
