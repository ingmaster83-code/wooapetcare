#!/usr/bin/env python3
"""
process_data.py (우아펫케어) - 행안부 LOCALDATA 동물판매업·동물위탁관리업 CSV(영업/정상)를 가공한다.
입력: data/raw/{animal_sales,animal_boarding}.csv   출력: _rawdata/pc_{시도}.json, search_index.json
종류: 동물판매업 → 조류·관상어·특수동물(상호 키워드) / 펫샵·분양(기본). 동물위탁관리업 → 동물병원 병설 → 애견카페 → 유치원·훈련 → 애견호텔·돌봄 → 펫미용·기타 위탁(기본).
상호 키워드 기준이라 실제 서비스와 다를 수 있다(페이지 문구에 명시).
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_localdata import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
CATMETA = {
    "펫샵·분양": ("petshop", "🐶"), "조류·관상어·특수동물": ("exotic", "🦜"), "애견호텔·돌봄": ("hotel", "🏨"), "유치원·훈련": ("kindergarten", "🎓"),
    "애견카페": ("cafe", "☕"), "동물병원 병설": ("clinic", "🏥"), "펫미용·기타 위탁": ("etc", "🐾"),
}
RE_EXOTIC = re.compile(r"조류|앵무|새|열대어|관상어|수족관|아쿠아|금붕어|물고기|파충류|도마뱀|곤충|햄스터|토끼|고슴도치|aqua|bird", re.I)
RE_CLINIC = re.compile(r"동물병원|동물의료|메디컬|병원|클리닉|vet", re.I)
RE_CAFE = re.compile(r"카페|cafe|커피", re.I)
RE_SCHOOL = re.compile(r"유치원|댕치원|멍치원|냥치원|린이집|학당|등교|훈련|스쿨|아카데미|학교|교육|school|training", re.I)
RE_HOTEL = re.compile(r"호텔|호스텔|hotel|돌봄|케어|care|위탁|펜션|스테이|캠프|리조트|보육|놀이터", re.I)
RE_SHOP = re.compile(r"분양|애견샵|펫샵|샵|숍|shop|용품|스토어", re.I)
RE_GROOM = re.compile(r"미용|살롱|그루밍|뷰티|목욕|스파|salon|grooming", re.I)


def classify_sales(name):
    return "조류·관상어·특수동물" if RE_EXOTIC.search(name) else "펫샵·분양"


def classify_boarding(name):
    if RE_CLINIC.search(name):
        return "동물병원 병설"
    if RE_CAFE.search(name):
        return "애견카페"
    if RE_SCHOOL.search(name):
        return "유치원·훈련"
    if RE_HOTEL.search(name):
        return "애견호텔·돌봄"
    if RE_GROOM.search(name):
        return "펫미용·기타 위탁"
    if RE_SHOP.search(name):
        return "펫샵·분양"
    return "펫미용·기타 위탁"


def main():
    tf = make_transformer()
    records = []
    for fn, biz, fcls in (("animal_sales.csv", "동물판매업", classify_sales), ("animal_boarding.csv", "동물위탁관리업", classify_boarding)):
        for r in read_csv_rows(RAW / fn):
            if clean(r.get("영업상태명")) != "영업/정상":
                continue
            name = clean(r.get("사업장명"))
            cat = fcls(name)
            lat, lng = to_wgs(tf, r.get("좌표정보(X)"), r.get("좌표정보(Y)"))
            extras = [{"l": "등록 업종", "v": biz}]
            records.append(dict(name=name, cat=cat, road=r.get("도로명주소"), lot=r.get("지번주소"), tel=r.get("전화번호"),
                                permit=r.get("인허가일자"), upd=clean(r.get("최종수정시점"))[:10], lat=lat, lng=lng,
                                extras=extras, hrows=[], note="", subtype=biz))
    finalize(records, ROOT / "_rawdata", "pc", ROOT, CATMETA)


if __name__ == "__main__":
    main()
