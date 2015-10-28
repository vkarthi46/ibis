# Copyright 2015 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import pytest

from pandas.util.testing import assert_frame_equal
import pandas as pd

from ibis.compat import unittest
from ibis.common import IbisTypeError
from ibis.impala.client import pandas_to_ibis_schema, DataFrameWriter
from ibis.impala.tests.common import ImpalaE2E
import ibis.expr.datatypes as dt
import ibis.expr.types as ir
import ibis.util as util
import ibis


class TestPandasTypeInterop(unittest.TestCase):

    def test_series_to_ibis_literal(self):
        values = [1, 2, 3, 4]
        s = pd.Series(values)

        expr = ir.as_value_expr(s)
        expected = ir.sequence(list(s))
        assert expr.equals(expected)


class TestPandasSchemaInference(unittest.TestCase):

    def test_dtype_bool(self):
        df = pd.DataFrame({'col': [True, False, False]})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'boolean')])
        assert inferred == expected

    def test_dtype_int8(self):
        df = pd.DataFrame({'col': np.int8([-3, 9, 17])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int8')])
        assert inferred == expected

    def test_dtype_int16(self):
        df = pd.DataFrame({'col': np.int16([-5, 0, 12])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int16')])
        assert inferred == expected

    def test_dtype_int32(self):
        df = pd.DataFrame({'col': np.int32([-12, 3, 25000])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int32')])
        assert inferred == expected

    def test_dtype_int64(self):
        df = pd.DataFrame({'col': np.int64([102, 67228734, -0])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int64')])
        assert inferred == expected

    def test_dtype_float32(self):
        df = pd.DataFrame({'col': np.float32([45e-3, -0.4, 99.])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'float')])
        assert inferred == expected

    def test_dtype_float64(self):
        df = pd.DataFrame({'col': np.float64([-3e43, 43., 10000000.])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'double')])
        assert inferred == expected

    def test_dtype_uint8(self):
        df = pd.DataFrame({'col': np.uint8([3, 0, 16])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int16')])
        assert inferred == expected

    def test_dtype_uint16(self):
        df = pd.DataFrame({'col': np.uint16([5569, 1, 33])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int32')])
        assert inferred == expected

    def test_dtype_uint32(self):
        df = pd.DataFrame({'col': np.uint32([100, 0, 6])})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int64')])
        assert inferred == expected

    def test_dtype_uint64(self):
        df = pd.DataFrame({'col': np.uint64([666, 2, 3])})
        with self.assertRaises(IbisTypeError):
            inferred = pandas_to_ibis_schema(df)  # noqa

    def test_dtype_datetime64(self):
        df = pd.DataFrame({
            'col': [pd.Timestamp('2010-11-01 00:01:00'),
                    pd.Timestamp('2010-11-01 00:02:00.1000'),
                    pd.Timestamp('2010-11-01 00:03:00.300000')]})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'timestamp')])
        assert inferred == expected

    def test_dtype_timedelta64(self):
        df = pd.DataFrame({
            'col': [pd.Timedelta('1 days'),
                    pd.Timedelta('-1 days 2 min 3us'),
                    pd.Timedelta('-2 days +23:57:59.999997')]})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'int64')])
        assert inferred == expected

    def test_dtype_string(self):
        df = pd.DataFrame({'col': ['foo', 'bar', 'hello']})
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', 'string')])
        assert inferred == expected

    def test_dtype_categorical(self):
        df = pd.DataFrame({'col': ['a', 'b', 'c', 'a']}, dtype='category')
        inferred = pandas_to_ibis_schema(df)
        expected = ibis.schema([('col', dt.Category(3))])
        assert inferred == expected


exhaustive_df = pd.DataFrame({
    'bigint_col': np.int64([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
    'bool_col': np.bool_([True, False, True, False, True, None,
                          True, False, True, False]),
    'date_string_col': ['11/01/10', None, '11/01/10', '11/01/10',
                        '11/01/10', '11/01/10', '11/01/10', '11/01/10',
                        '11/01/10', '11/01/10'],
    'double_col': np.float64([0.0, 10.1, None, 30.299999999999997,
                              40.399999999999999, 50.5, 60.599999999999994,
                              70.700000000000003, 80.799999999999997,
                              90.899999999999991]),
    'float_col': np.float32([None, 1.1000000238418579, 2.2000000476837158,
                             3.2999999523162842, 4.4000000953674316, 5.5,
                             6.5999999046325684, 7.6999998092651367,
                             8.8000001907348633,
                             9.8999996185302734]),
    'int_col': np.int32([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    'month': [11, 11, 11, 11, 2, 11, 11, 11, 11, 11],
    'smallint_col': np.int16([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    'string_col': ['0', '1', None, 'double , whammy', '4', '5',
                   '6', '7', '8', '9'],
    'timestamp_col': [pd.Timestamp('2010-11-01 00:00:00'),
                      None,
                      pd.Timestamp('2010-11-01 00:02:00.100000'),
                      pd.Timestamp('2010-11-01 00:03:00.300000'),
                      pd.Timestamp('2010-11-01 00:04:00.600000'),
                      pd.Timestamp('2010-11-01 00:05:00.100000'),
                      pd.Timestamp('2010-11-01 00:06:00.150000'),
                      pd.Timestamp('2010-11-01 00:07:00.210000'),
                      pd.Timestamp('2010-11-01 00:08:00.280000'),
                      pd.Timestamp('2010-11-01 00:09:00.360000')],
    'tinyint_col': np.int8([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    'year': [2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010]})


class TestPandasInterop(ImpalaE2E, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPandasInterop, cls).setUpClass()
        cls.alltypes = cls.alltypes.execute()

    def test_alltypes_roundtrip(self):
        self._check_roundtrip(self.alltypes)

    def test_writer_cleanup_deletes_hdfs_dir(self):
        writer = DataFrameWriter(self.con, self.alltypes)
        writer.write_csv()

        path = writer.csv_dir
        assert self.con.hdfs.exists(path)

        writer.cleanup()
        assert not self.con.hdfs.exists(path)

        # noop
        writer.cleanup()
        assert not self.con.hdfs.exists(path)

    def test_create_table_from_dataframe(self):
        tname = 'tmp_pandas_{0}'.format(util.guid())
        self.con.create_table(tname, self.alltypes, database=self.tmp_db)
        self.temp_tables.append(tname)

        table = self.con.table(tname, database=self.tmp_db)
        df = table.execute()
        assert_frame_equal(df, self.alltypes)

    def test_insert(self):
        schema = pandas_to_ibis_schema(exhaustive_df)

        table_name = 'tmp_pandas_{0}'.format(util.guid())
        self.con.create_table(table_name, database=self.tmp_db,
                              schema=schema)
        self.temp_tables.append(table_name)

        self.con.insert(table_name, exhaustive_df.iloc[:4],
                        database=self.tmp_db)
        self.con.insert(table_name, exhaustive_df.iloc[4:],
                        database=self.tmp_db)

        table = self.con.table(table_name, database=self.tmp_db)

        result = (table.execute()
                  .sort_index(by='tinyint_col')
                  .reset_index(drop=True))
        assert_frame_equal(result, exhaustive_df)

    def test_insert_partition(self):
        # overwrite

        # no overwrite
        pass

    def test_round_trip_exhaustive(self):
        self._check_roundtrip(exhaustive_df)

    def _check_roundtrip(self, df):
        writer = DataFrameWriter(self.con, df)
        writer.write_csv()

        table = writer.delimited_table()
        df2 = table.execute()

        assert_frame_equal(df2, df)

    def test_round_trip_missing_type_promotion(self):
        pytest.skip('unfinished')

        # prepare Impala table with missing ints
        # TODO: switch to self.con.raw_sql once #412 is fixed
        create_query = ('CREATE TABLE {0}.missing_ints '
                        '  (tinyint_col TINYINT, bigint_col BIGINT) '
                        'STORED AS PARQUET'.format(self.tmp_db))
        insert_query = ('INSERT INTO {0}.missing_ints '
                        'VALUES (NULL, 3), (-5, NULL), (19, 444444)'.format(
                            self.tmp_db))
        self.con.con.cursor.execute(create_query)
        self.con.con.cursor.execute(insert_query)

        table = self.con.table('missing_ints', database=self.tmp_db)
        df = table.execute()  # noqa  # REMOVE LATER

        # WHAT NOW?
