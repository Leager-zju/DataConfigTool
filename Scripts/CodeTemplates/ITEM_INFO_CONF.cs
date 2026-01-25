
using System.Collections.Generic;
using System.IO;

namespace SampleProject.Config
{
    public struct ITEM_INFO_CONF_DATA
    {
        public int id;
        public string name;
        public string type;
        public float value;
        public bool stackable;
        public int max_stack;
        public List<string> tags;
        public Dictionary<string, float> properties;
    }

    public class ITEM_INFO_CONF : IConfig
    {
        private readonly Dictionary<int, ITEM_INFO_CONF_DATA> _datas = [];

        public string FileName { get => "res://Data/Config/ITEM_INFO_CONF/ITEM_INFO_CONF.yaml"; set => throw new System.InvalidOperationException(); }

        public void LoadFromFile() => BinaryConfigReader.ReadEncryptedFile(FileName, ParseData);
        public ITEM_INFO_CONF_DATA GetData(int id) => _datas[id];
        public Dictionary<int, ITEM_INFO_CONF_DATA> GetAllDatas() => _datas;

        private void ParseData(BinaryReader reader)
        {
            uint rowCount = reader.ReadUInt32();
            for (int i = 0; i < rowCount; i++)
            {
                var id = (int)BinaryConfigReader.ReadValue(reader, ValueType.INT);
                var rowData = new ITEM_INFO_CONF_DATA
                {
                    id = (int)BinaryConfigReader.ReadValue(reader, ValueType.INT),
                    name = BinaryConfigReader.ReadString(reader),
                    type = BinaryConfigReader.ReadString(reader),
                    value = (float)BinaryConfigReader.ReadValue(reader, ValueType.FLOAT),
                    stackable = (bool)BinaryConfigReader.ReadValue(reader, ValueType.BOOL),
                    max_stack = (int)BinaryConfigReader.ReadValue(reader, ValueType.INT),
                    tags = BinaryConfigReader.ReadValue(reader, ValueType.LIST) as List<string>,
                    properties = BinaryConfigReader.ReadValue(reader, ValueType.DICT) as Dictionary<string, float>,

                };

                _datas.Add(id, rowData);
            }
        }
    }
}
                