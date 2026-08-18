// Конфиг витрины. На этапе сборки токен авто-извлекается из бандла l.bezlimit.ru
// и подставляется сюда; значение ниже — хардкод-фолбэк (публичный токен из их фронта).
window.NUMSTORE_CONFIG = {
  API_BASE: "https://api.store.bezlimit.ru/v2",
  // Basic-токен Безлимит (публичный, из их JS-бандла). Обновляется сборкой.
  API_TOKEN: "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==",
  // Реф-id партнёра. Идёт в тело брони как user_id (привязка комиссии) и в реф-ссылку store.
  REF_ID: "800848",
  REF_STORE_URL: "https://l.bezlimit.ru/store/800848",
};
