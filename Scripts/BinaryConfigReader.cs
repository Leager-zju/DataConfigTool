using System.Text;
using System.Security.Cryptography;
using System.Text.Json;

namespace DataConfigTool.Config
{
    public interface IConfig
    {
        public string FileName { get; set; }
        public void LoadFromFile();
    }

    public class BinaryConfigReader
    {
        private static readonly byte[] ENCRYPTED_KEY = Encoding.UTF8.GetBytes("your-32-byte-secret-key-here!123");
        /// <summary>
        /// 读取加密的二进制配置文件
        /// </summary>
        /// <param name="filePath">文件路径</param>
        /// <param name="encryptionKey">加密密钥（32字节）</param>
        /// <returns>配置表数据</returns>
        internal static void ReadEncryptedFile(string filePath, Action<BinaryReader> readFunc)
        {
            using var fileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
            using var binaryReader = new BinaryReader(fileStream);
            // 读取魔数
            byte[] magic = binaryReader.ReadBytes(4);
            if (Encoding.ASCII.GetString(magic) != "SHET")
            {
                throw new InvalidDataException("无效的文件格式");
            }

            // 读取数据长度
            uint dataLength = binaryReader.ReadUInt32();

            // 读取数据
            byte[] data = binaryReader.ReadBytes((int)dataLength);

            data = DecryptAES(data);

            // 解析数据
            using var memoryStream = new MemoryStream(data);
            using var dataReader = new BinaryReader(memoryStream);
            readFunc(dataReader);
        }

        /// <summary>
        /// AES-CBC解密
        /// </summary>
        private static byte[] DecryptAES(byte[] encryptedData)
        {
            using var aes = Aes.Create();
            aes.Key = ENCRYPTED_KEY;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;

            // 提取IV（前16字节）
            byte[] iv = new byte[16];
            Array.Copy(encryptedData, iv, 16);
            aes.IV = iv;

            // 提取加密数据（剩余部分）
            byte[] cipherText = new byte[encryptedData.Length - 16];
            Array.Copy(encryptedData, 16, cipherText, 0, cipherText.Length);

            using var decryptor = aes.CreateDecryptor();
            using var memoryStream = new MemoryStream(cipherText);
            using var cryptoStream = new CryptoStream(memoryStream, decryptor, CryptoStreamMode.Read);
            using var resultStream = new MemoryStream();
            cryptoStream.CopyTo(resultStream);
            return resultStream.ToArray();
        }

        /// <summary>
        /// 读取字符串
        /// </summary>
        public static string ReadString(BinaryReader reader)
        {
            uint length = reader.ReadUInt32();
            byte[] data = reader.ReadBytes((int)length);
            return Encoding.UTF8.GetString(data);
        }

        /// <summary>
        /// 读取值
        /// </summary>
        public static object ReadValue(BinaryReader reader, ValueType valueType)
        {
            byte isNull = reader.ReadByte();
            if (isNull == 0)
            {
                return null;
            }

            switch (valueType)
            {
                case ValueType.INT:
                    return reader.ReadInt32();

                case ValueType.FLOAT:
                    return reader.ReadSingle();

                case ValueType.STRING:
                    return ReadString(reader);

                case ValueType.BOOL:
                    return reader.ReadByte() == 1;

                case ValueType.LIST:
                    string listJson = ReadString(reader);
                    return JsonSerializer.Deserialize<List<object>>(listJson);

                case ValueType.DICT:
                    string dictJson = ReadString(reader);
                    return JsonSerializer.Deserialize<Dictionary<string, object>>(dictJson);

                default:
                    return ReadString(reader);
            }
        }
    }
}