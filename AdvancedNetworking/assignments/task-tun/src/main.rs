// Because there are two input sources (TUN device and UDP socket),
// MIO or tokio multitasking is needed for parallel waiting from
// different sources. You may also try to use threads.
use mio::{ Events, Interest, Poll, net::UdpSocket, Token };


fn main() -> std::io::Result<()> {
    // Create and configure the TUN device
    let mut config = tun::Configuration::default();
    config
        .tun_name("tun0")   // Interface name
        .address(/* local address */)  // Assign IP to the interface
        .destination(/* remote address */) // Peer address
        .netmask("255.255.255.0") // Subnet mask
        .up(); // Bring interface up

    let mut dev = tun::create(&config).expect("Failed to create TUN device");

    let mut socket = UdpSocket::bind(args.udpbind().parse().unwrap())?;

    /*
     * Start waiting for data from both dev and socket. Using MIO event handling
     * loop should be quite straight forward way to do this.
     * When data arrives from either source, pass it forward, following the
     * instructions in the task description.
     */
}
