import json

def build_tender_extract_prompt(file_name: str, full_text: str, sections: list[dict]) -> str:
    sections_text = json.dumps(sections, ensure_ascii=False, indent=2)
    return f"""浣犳槸涓€涓嫑鏍囨枃浠惰В鏋愬姪鎵嬨€?璇锋牴鎹粰瀹氱殑鎷涙爣鏂囦欢鍐呭锛屾彁鍙栧叧閿俊鎭紝骞朵弗鏍艰繑鍥?JSON銆?涓嶈杈撳嚭瑙ｉ噴锛屼笉瑕佽緭鍑?markdown 浠ｇ爜鍧楋紝涓嶈琛ュ厖澶氫綑鏂囧瓧銆?
蹇呴』杩斿洖濡備笅缁撴瀯锛?{{
  \"file_name\": \"{file_name}\",
  \"project_name\": \"\",
  \"tender_company\": \"\",
  \"deadline\": \"\",
  \"qualification_requirements\": [],
  \"technical_requirements\": [],
  \"business_requirements\": [],
  \"scoring_rules\": [],
  \"sections\": []
}}

瀛楁瑕佹眰锛?- project_name锛氶」鐩悕绉?- tender_company锛氭嫑鏍囧崟浣?- deadline锛氭姇鏍囨埅姝㈡椂闂达紝娌℃湁灏辩暀绌哄瓧绗︿覆
- qualification_requirements锛氳祫璐ㄨ姹傦紝鎻愬彇涓哄瓧绗︿覆鏁扮粍
- technical_requirements锛氭妧鏈姹傦紝鎻愬彇涓哄瓧绗︿覆鏁扮粍
- business_requirements锛氬晢鍔¤姹傦紝鎻愬彇涓哄瓧绗︿覆鏁扮粍
- scoring_rules锛氳瘎鍒嗗姙娉曪紝鎻愬彇涓哄瓧绗︿覆鏁扮粍
- sections锛氫繚鎸佺┖鏁扮粍鍗冲彲锛屾渶缁堢敱绋嬪簭鍐欏洖

濡傛灉鏌愬瓧娈垫棤娉曠‘瀹氾紝璇蜂娇鐢ㄧ┖瀛楃涓叉垨绌烘暟缁勶紝涓嶈缂栭€犮€?
鏂囦欢鍚嶏細{file_name}

绔犺妭淇℃伅锛?{sections_text}

鍏ㄦ枃锛堝彲鑳借鎴柇锛夛細
{full_text}
"""
