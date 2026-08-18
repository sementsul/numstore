// Конфиг витрины. На этапе сборки токен авто-извлекается из бандла l.bezlimit.ru
// и подставляется сюда; значение ниже — хардкод-фолбэк (публичный токен из их фронта).
window.NUMSTORE_CONFIG = {
  API_BASE: "https://api.store.bezlimit.ru/v2",
  // Basic-токен Безлимит (публичный, из их JS-бандла). Обновляется сборкой.
  API_TOKEN: "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==",
  // Реферальный магазин партнёра — сюда ведёт кнопка «купить» (несёт реф-id 800848).
  REF_ID: "800848",
  REF_STORE_URL: "https://l.bezlimit.ru/store/800848",
};
