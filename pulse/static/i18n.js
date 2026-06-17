/* Pulse i18n — Traditional Chinese only */
const T = {
  title: "Pulse — 2026 世界盃 × 預測市場",
  brandSub: "世界盃 × Polymarket",
  brandTag: "即時更新",
  heroEyebrow: "比賽 + 市場",
  heroHead: "賽場是一種真相。市場是另一種。我們把它們並排呈現。",
  heroSub: "把當下的比賽狀態、Polymarket 的即時賠率、以及價格波動放在同一個螢幕上。",
  heroH1_1: "賽場是一種真相。",
  heroH1_2: "市場是另一種。",
  heroH1_3: "我們把它們並排呈現。",
  lead: "把當下的比賽狀態、Polymarket 的即時賠率、以及價格波動放在同一個螢幕上。",
  statLive: "直播中",
  statMarkets: "追蹤市場",
  statEdge: "最大邊際",
  statUpdate: "最後更新",
  secMatches: "賽事 × 市場",
  secMatchesHint: "點擊篩選切換類別",
  secMoved: "市場變動",
  secMovedHint: "近期最大波動",
  secHot: "資金流向",
  secHotHint: "Polymarket 熱門足球市場",
  marketsMoved: "市場變動",
  marketsMovedHint: "近期最大波動",
  whereMoney: "資金流向",
  whereMoneyHint: "Polymarket 熱門足球市場",
  filterAll: "全部",
  filterLive: "直播",
  filterUpcoming: "即將",
  filterFinal: "完賽",
  waitingPoll: "等待首次輪詢…",
  fetchingMatches: "正在獲取賽事…",
  fetching: "正在獲取…",
  noMoves: "暫無顯著波動",
  noMarkets: "暫無獨立市場",
  noMatchFilter: "目前沒有符合此篩選的賽事",
  connecting: "正在連線…",
  live: "已連線",
  reconnecting: "重新連線中…",
  disconnected: "已斷線",
  autoRefresh: "自動刷新 · WebSocket",
  stateLive: "直播中",
  stateSoon: "即將",
  stateFT: "完賽",
  kickoff: "開球",
  edgeLabel: "邊際",
  noMarket: "— 沒有對應市場 —",
  vol24h: "24小時成交量",
  justNow: "剛剛",
  secAgo: "秒前",
  minAgo: "分鐘前",
  hrAgo: "小時前",
  footerTitle: "Pulse — 為足球博彩玩家而生的即時數據儀表板",
  footerBuilt: "由 parkl 構建 · ClawProject/pulse",
  footerData: "資料來源：ESPN（公開）+ Polymarket Gamma（公開）",
};

/* Team + venue + market-term translations */
const TEAM_NAMES = {
  "Argentina": "阿根廷", "Australia": "澳洲", "Austria": "奧地利",
  "Belgium": "比利時", "Brazil": "巴西", "Cameroon": "喀麥隆",
  "Canada": "加拿大", "Chile": "智利", "Colombia": "哥倫比亞",
  "Costa Rica": "哥斯達黎加", "Croatia": "克羅地亞", "Curaçao": "古拉索",
  "Denmark": "丹麥", "Ecuador": "厄瓜多爾", "Egypt": "埃及",
  "England": "英格蘭", "France": "法國", "Germany": "德國",
  "Ghana": "加納", "Haiti": "海地", "Iran": "伊朗",
  "Iraq": "伊拉克", "Italy": "意大利", "Japan": "日本",
  "Korea Republic": "南韓", "South Korea": "南韓",
  "Mexico": "墨西哥", "Morocco": "摩洛哥", "Netherlands": "荷蘭",
  "New Zealand": "新西蘭", "Nigeria": "尼日利亞", "Norway": "挪威",
  "Paraguay": "巴拉圭", "Peru": "秘魯", "Poland": "波蘭",
  "Portugal": "葡萄牙", "Qatar": "卡塔爾", "Saudi Arabia": "沙地阿拉伯",
  "Scotland": "蘇格蘭", "Senegal": "塞內加爾", "Serbia": "塞爾維亞",
  "South Africa": "南非", "Spain": "西班牙", "Sweden": "瑞典",
  "Switzerland": "瑞士", "Tunisia": "突尼斯", "Turkey": "土耳其",
  "Türkiye": "土耳其", "Ukraine": "烏克蘭",
  "United Arab Emirates": "阿聯酋", "United States": "美國", "USA": "美國",
  "Uruguay": "烏拉圭", "Venezuela": "委內瑞拉", "Wales": "威爾斯",
  "ARG": "阿根廷", "AUS": "澳洲", "AUT": "奧地利", "BEL": "比利時",
  "BRA": "巴西", "CAN": "加拿大", "CMR": "喀麥隆", "CHI": "智利",
  "COL": "哥倫比亞", "CRC": "哥斯達黎加", "CRO": "克羅地亞",
  "CUW": "古拉索", "DEN": "丹麥", "ECU": "厄瓜多爾", "EGY": "埃及",
  "ENG": "英格蘭", "ESP": "西班牙", "FRA": "法國", "GER": "德國",
  "GHA": "加納", "HAI": "海地", "IRN": "伊朗", "IRQ": "伊拉克",
  "ITA": "意大利", "JPN": "日本", "KOR": "南韓", "KSA": "沙地阿拉伯",
  "MAR": "摩洛哥", "MEX": "墨西哥", "NED": "荷蘭", "NGA": "尼日利亞",
  "NOR": "挪威", "NZL": "新西蘭", "PAR": "巴拉圭", "PER": "秘魯",
  "POL": "波蘭", "POR": "葡萄牙", "QAT": "卡塔爾", "SCO": "蘇格蘭",
  "SEN": "塞內加爾", "SRB": "塞爾維亞", "SUI": "瑞士", "SWE": "瑞典",
  "TUN": "突尼斯", "TUR": "土耳其", "UKR": "烏克蘭", "URU": "烏拉圭",
  "USA": "美國", "VEN": "委內瑞拉", "WAL": "威爾斯",
  "Yes": "是", "No": "否", "Over": "大", "Under": "小", "Draw": "和局",
  "Home": "主隊", "Away": "客隊",
  "Levi's Stadium": "李維斯體育場",
  "MetLife Stadium": "大都會人壽體育場",
  "AT&T Stadium": "AT&T 體育場",
  "SoFi Stadium": "SoFi 體育場",
  "Hard Rock Stadium": "硬石體育場",
  "Gillette Stadium": "吉列體育場",
  "NRG Stadium": "NRG 體育場",
  "Mercedes-Benz Stadium": "梅賽德斯-平治體育場",
  "State Farm Stadium": "州立農業體育場",
  "Arrowhead Stadium": "箭頭體育場",
  "Lincoln Financial Field": "林肯金融球場",
  "TQL Stadium": "TQL 體育場",
  "GEHA Field at Arrowhead Stadium": "GEHA 箭頭體育場",
  "Children's Mercy Park": "兒童慈悲公園",
  "Q2 Stadium": "Q2 體育場",
  "BC Place": "BC 體育場",
  "Estadio Azteca": "阿茲特克體育場",
  "Estadio BBVA": "BBVA 體育場",
  "Estadio Akron": "阿克龍體育場",
  "Estadio de Guadalajara": "瓜達拉哈拉體育場",
  "Estadio Universitario": "大學城體育場",
  "Rose Bowl": "玫瑰碗體育場",
  "Stanford Stadium": "史丹福體育場",
  "Allegiant Stadium": "忠誠體育場",
};

function t(key) { return T[key] || key; }

function tname(englishName) {
  if (!englishName) return "—";
  return TEAM_NAMES[englishName] || englishName;
}

/* Apply translations on DOMContentLoaded (before app.js renders) */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    var k = el.getAttribute("data-i18n");
    if (k && T[k]) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = T[k];
      } else if (el.hasAttribute("data-i18n-html")) {
        el.innerHTML = T[k].replace(/\n/g, "<br/>");
      } else {
        el.textContent = T[k];
      }
    }
  });
  document.title = T.title;
  document.documentElement.lang = "zh-Hant";
});
