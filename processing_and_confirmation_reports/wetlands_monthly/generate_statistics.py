import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from rasterio.plot import show_hist
from glob import glob
import pathlib
import boto3
import pandas as pd
import calendar
import seaborn as sns
import json

# session_veda_smce = boto3.session.Session()
session_veda_smce = boto3.Session(
    aws_access_key_id="ASIAWOY6ET4O7M4SQNUF",
    aws_secret_access_key="2LDOx2piH+1sBxR5TVgzoQpTGhj58EpXnafmscBP",
    aws_session_token="IQoJb3JpZ2luX2VjEOf//////////wEaCXVzLXdlc3QtMiJHMEUCIQDYk+NfUFueTq0v86RreUN0LWWsXVQiguEUHt6SWbOpWwIgURjUYGQk+ad4moMFtCO9ybjONz5uQ1rk4lV678QF63Yq+AEIj///////////ARAAGgw0NDQwNTU0NjE2NjEiDOr4YGUp5ccPuBIGwCrMAQf6nDH5vc46etId40+h/5K97E4MngVbInv9nmOzfuBwLVrtvJf8u5gJjqPWOIzZMJ/rzAYQqm3GQ3mD1Yf0fTDbq0wx3RWSfW4nbQtIR8keVcNKb9EgmxSkdUbPbXG/rihynuAMYA2VEshOQZ49v1izDS+uQUJnRo+HR22XOgyHM4lEKDcHdJIC1KZLPQd9QJRFP88Dor8olI/tsLs7AA+Sl4tN7W3YncBz0jwqj2q/JinBnQNoi21lfFzk1/RV4AKK73JNxw8t923XMzDPnsmmBjqYAdShFmQGip2XjkOySbd9+YkO05hu/Jq+tddU9cyKpO4v3mfpC+Fg+m8a2659wKHiWAl9gmy8uK9GiEU1NrNWGJuED7RRyE/l2K5eDcV1PzMQb1DK2JKmUtUC+FmCO8hjN4I50lvLVS0ncEWfEfOrK5kKGUasiAXVXPJxC7sAtI68phlE6qBocJ3jhj2XrBicFWIXOlPDwQ/Z",
)
s3_client_veda_smce = session_veda_smce.client("s3")
raster_io_session = rasterio.env.Env(
    aws_access_key_id="ASIAWOY6ET4O7M4SQNUF",
    aws_secret_access_key="2LDOx2piH+1sBxR5TVgzoQpTGhj58EpXnafmscBP",
    aws_session_token="IQoJb3JpZ2luX2VjEOf//////////wEaCXVzLXdlc3QtMiJHMEUCIQDYk+NfUFueTq0v86RreUN0LWWsXVQiguEUHt6SWbOpWwIgURjUYGQk+ad4moMFtCO9ybjONz5uQ1rk4lV678QF63Yq+AEIj///////////ARAAGgw0NDQwNTU0NjE2NjEiDOr4YGUp5ccPuBIGwCrMAQf6nDH5vc46etId40+h/5K97E4MngVbInv9nmOzfuBwLVrtvJf8u5gJjqPWOIzZMJ/rzAYQqm3GQ3mD1Yf0fTDbq0wx3RWSfW4nbQtIR8keVcNKb9EgmxSkdUbPbXG/rihynuAMYA2VEshOQZ49v1izDS+uQUJnRo+HR22XOgyHM4lEKDcHdJIC1KZLPQd9QJRFP88Dor8olI/tsLs7AA+Sl4tN7W3YncBz0jwqj2q/JinBnQNoi21lfFzk1/RV4AKK73JNxw8t923XMzDPnsmmBjqYAdShFmQGip2XjkOySbd9+YkO05hu/Jq+tddU9cyKpO4v3mfpC+Fg+m8a2659wKHiWAl9gmy8uK9GiEU1NrNWGJuED7RRyE/l2K5eDcV1PzMQb1DK2JKmUtUC+FmCO8hjN4I50lvLVS0ncEWfEfOrK5kKGUasiAXVXPJxC7sAtI68phlE6qBocJ3jhj2XrBicFWIXOlPDwQ/Z",
)
bucket_name = "ghgc-data-store-dev"

keys = []
resp = s3_client_veda_smce.list_objects_v2(
    Bucket=bucket_name, Prefix="NASA_GSFC_ch4_wetlands_monthly/"
)
for obj in resp["Contents"]:
    if obj["Key"].endswith(".tif"):
        keys.append(obj["Key"])

# List all TIFF files in the folder
tif_files = glob("../../data/wetlands-monthly/*.nc", recursive=True)
session = rasterio.env.Env()
summary_dict_netcdf, summary_dict_cog = {}, {}
overall_stats_netcdf, overall_stats_cog = {}, {}
full_data_df_netcdf, full_data_df_cog = pd.DataFrame(), pd.DataFrame()

# Iterate over each TIFF file
for tif_file in tif_files:
    file_name = pathlib.Path(tif_file).name[:-3]
    pdf_path = f"summary_reports/{pathlib.Path(tif_file).parent.name}/{pathlib.Path(tif_file).name[:-3]}.pdf"
    # pdf_file = PdfFile(pdf_path)

    # Open the TIFF file
    with rasterio.open(tif_file) as src:
        for band in src.indexes:
            idx = pd.MultiIndex.from_product(
                [
                    [tif_file],
                    [band],
                    [x for x in np.arange(1, src.height + 1)],
                ]
            )
            # Read the raster data
            raster_data = src.read(band)
            raster_data[raster_data == -9999] = np.nan
            temp = pd.DataFrame(index=idx, data=raster_data)
            full_data_df_netcdf = full_data_df_netcdf._append(temp, ignore_index=False)

            # Calculate summary statistics
            min_value = temp.values.min()
            max_value = temp.values.max()
            mean_value = temp.values.mean()
            std_value = temp.values.std()

            summary_dict_netcdf[
                f'{tif_file.split(".")[-2]}_{calendar.month_name[band]}'
            ] = {
                "min_value": str(min_value),
                "max_value": str(max_value),
                "mean_value": str(mean_value),
                "std_value": str(std_value),
            }

for key in keys:
    with raster_io_session:
        s3_file = s3_client_veda_smce.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": key}
        )
        with rasterio.open(s3_file) as src:
            for band in src.indexes:
                idx = pd.MultiIndex.from_product(
                    [
                        [s3_file.split("_")[-1]],
                        [s3_file.split("_")[-1][5]],
                        [x for x in np.arange(1, src.height + 1)],
                    ]
                )
                # Read the raster data
                raster_data = src.read(band)
                raster_data[raster_data == -9999] = np.nan
                temp = pd.DataFrame(index=idx, data=raster_data)
                full_data_df_cog = full_data_df_cog._append(temp, ignore_index=False)

                # Calculate summary statistics
                min_value = temp.values.min()
                max_value = temp.values.max()
                mean_value = temp.values.mean()
                std_value = temp.values.std()

                summary_dict_cog[
                    f'{s3_file.split("_")[-1][:4]}_{calendar.month_name[int(s3_file.split("_")[-1][4:6])]}'
                ] = {
                    "min_value": str(min_value),
                    "max_value": str(max_value),
                    "mean_value": str(mean_value),
                    "std_value": str(std_value),
                }


overall_stats_netcdf["min_value"] = str(full_data_df_netcdf.values.min())
overall_stats_netcdf["max_value"] = str(full_data_df_netcdf.values.max())
overall_stats_netcdf["mean_value"] = str(full_data_df_netcdf.values.mean())
overall_stats_netcdf["std_value"] = str(full_data_df_netcdf.values.std())

overall_stats_cog["min_value"] = str(full_data_df_cog.values.min())
overall_stats_cog["max_value"] = str(full_data_df_cog.values.max())
overall_stats_cog["mean_value"] = str(full_data_df_cog.values.mean())
overall_stats_cog["std_value"] = str(full_data_df_cog.values.std())


with open(
    "monthly_stats.json",
    "w",
) as fp:
    json.dump(summary_dict_netcdf, fp)
    json.dump(summary_dict_cog, fp)

with open("overall_stats.json", "w") as fp:
    json.dump(overall_stats_netcdf, fp)
    json.dump(overall_stats_cog, fp)

fig, ax = plt.subplots(2, 2, figsize=(10, 10))
plt.Figure(figsize=(10, 10))
sns.histplot(data=full_data_df_netcdf, kde=False, bins=10, legend=False, ax=ax[0][0])
ax[0][0].set_title("distribution plot for overall raw data")

sns.histplot(data=full_data_df_cog, kde=False, bins=10, legend=False, ax=ax[0][1])
ax[0][1].set_title("distribution plot for overall cog data")

sns.histplot(
    data=summary_dict_netcdf["2009_January"],
    kde=False,
    bins=10,
    legend=False,
    ax=ax[1][0],
)
ax[1][0].set_title("distribution plot for 2009 January raw data")

sns.histplot(
    data=summary_dict_cog["2009_January"],
    kde=False,
    bins=10,
    legend=False,
    ax=ax[1][1],
)
ax[1][1].set_title("distribution plot for 2009 January cog data")


plt.savefig("stats_summary.png")
plt.show()
