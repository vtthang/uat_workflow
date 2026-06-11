import * as crypto from 'crypto';

export class DataGenerator {
  /**
   * Sinh email unique, traceable theo format: auto_<prefix>_<timestamp>_<rand>@test.com
   * Ví dụ: auto_createUser_20260529_A3F2@test.com
   */
  static email(prefix: string = 'test'): string {
    const ts = new Date().toISOString().replace(/[-T:.Z]/g, '').slice(0, 12);
    const rand = crypto.randomBytes(2).toString('hex').toUpperCase();
    return `auto_${prefix}_${ts}_${rand}@test.com`;
  }

  /**
   * Sinh chuỗi random có độ dài tùy chọn (chỉ ký tự alphanum)
   */
  static randomString(length: number = 8): string {
    return crypto.randomBytes(length).toString('hex').slice(0, length);
  }

  /**
   * Sinh số nguyên ngẫu nhiên trong khoảng [min, max]
   */
  static randomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  /**
   * Sinh tên người dùng traceable: auto_<prefix>_<timestamp>
   */
  static username(prefix: string = 'user'): string {
    const ts = Date.now();
    return `auto_${prefix}_${ts}`;
  }

  /**
   * Sinh timestamp hiện tại dạng YYYYMMDDHHMMSS
   */
  static timestamp(): string {
    return new Date().toISOString().replace(/[-T:.Z]/g, '').slice(0, 14);
  }

  /**
   * Sinh số điện thoại VN fake (không gọi được) để dùng trong test
   */
  static phoneVN(): string {
    const prefixes = ['090', '091', '093', '096', '097', '098', '070', '079', '077', '076', '078'];
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    const suffix = DataGenerator.randomInt(1000000, 9999999).toString();
    return `${prefix}${suffix}`;
  }
}
