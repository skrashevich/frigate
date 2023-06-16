export const ENV = import.meta.env.MODE;
export const API_HOST = ENV === 'production' ? '' : 'http://192.168.88.60:5000/';
