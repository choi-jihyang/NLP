/** 예시 데이터를 네트워크 응답처럼 돌려준다. 복사본을 넘겨 화면이 저장소를 직접 바꾸지 못하게 한다 */
export const respondWith = <T>(value: T, ms = 120): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(structuredClone(value)), ms))
