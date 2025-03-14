import random
import secrets

from copy import deepcopy
from itertools import combinations

WORTHS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
SUITS = ('Clubs', 'Diamonds', 'Hearts', 'Spades')
TOTAL_CARDS_IN_DECK = len(WORTHS) * len(SUITS)
SINGLE_CARD_ODDS = 1 / TOTAL_CARDS_IN_DECK
SINGLE_WORTH_ODDS = len(SUITS) / TOTAL_CARDS_IN_DECK
SINGLE_SUIT_ODDS = len(WORTHS) / TOTAL_CARDS_IN_DECK


class EndGame(Exception):
    pass


class WinningHand(object):
    def __init__(self):
        self.name = None  # readable name string used for printing data
        self.found = False  # boolean indicating if the hand has been found
        self.ranking = None  # integer indicating the 'rank' of the hand; higher is better
        self.high_value = None  # list of Cards that are the highest value cards meeting the criteria

        # self.close = False
        # self.odds = 0

    def get_sorted_cards(self, cards):
        """
            Return a sorted list, highest-value card to lowest-value card, from the passed-in list of cards.
        :param list[Card] cards: list of Cards to be sorted
        :return: Descending-sorted list of the given cards
        :rtype: list[Card]
        """
        copy_cards = deepcopy(cards)
        return sorted(copy_cards, key=lambda x: x.worth, reverse=True)

    @property
    def high_card(self):
        """
            Represents the highest-worth card in the hand (high-value).
        :return: Highest card in the hand
        :rtype: Card
        """
        return self.high_value[0] if self.high_value is not None else None

    def check_cards(self, cards):
        """
            Determine if the given cards match the criteria for the hand.  Return a boolean indicating if the given
            cards meet the hand criteria.

            Intended to be overwritten by subclasses.
        :param list[Card] cards:
        :return: Boolean indicating if the card meets the hand's criteria
        :rtype: bool
        """
        raise NotImplementedError()

    # @property
    # def outs(self):
    #     raise NotImplementedError()
    #
    # def calculate_odds(self, num_unseen_cards, remaining_community_cards):
    #     if remaining_community_cards > 0:
    #          raw = 1 - ((num_unseen_cards - self.outs) / num_unseen_cards) ** remaining_community_cards
    #     else:
    #         raw = 1 - ((num_unseen_cards - self.outs) / num_unseen_cards)
    #     self.odds = raw * 100


class HighCard(WinningHand):
    def __init__(self):
        super(HighCard, self).__init__()
        self.name = "High Card"
        self.ranking = 0

    def check_cards(self, cards):
        self.high_value = self.check_for_high_card(cards)
        self.found = True
        return self.found

    def check_for_high_card(self, cards):
        sorted_cards = self.get_sorted_cards(cards)
        return [sorted_cards[0], ]


class Pair(WinningHand):
    def __init__(self):
        super(Pair, self).__init__()
        self.name = "Pair"
        self.ranking = 1
        self.num_to_match = 2

    def check_cards(self, cards):
        matched_cards = self.check_for_worth_matches(cards)
        if matched_cards:
            self.found = True
            self.high_value = matched_cards

        return self.found

    def check_for_worth_matches(self, cards):
        """
            Utility function for checking for specific number of Cards' worth matches.  Checks the given cards to see if there
            are N matches of cards with the same worth, where N is defined as the class attribute num_to_match.
        :param list[Card] cards: list of Cards to check for worth matches.
        :return: list of Cards that have matching worth where the len of the list is equal to the class attribute num_to_match.
        :rtype: list[Card]
        """
        matches_found = []
        card_values = [x.worth for x in cards]
        if len(set(card_values)) < len(cards):
            sorted_cards = self.get_sorted_cards(cards)
            for _c in sorted_cards:
                if card_values.count(_c.worth) == self.num_to_match:
                    matches_found.append(_c)

        return matches_found[:self.num_to_match]


class TwoPair(Pair):
    def __init__(self):
        super(TwoPair, self).__init__()
        self.name = "Two Pair"
        self.ranking = 2

    def check_cards(self, cards):
        local_cards = deepcopy(cards)

        pair_1 = self.check_for_worth_matches(local_cards)
        if pair_1:
            self.close = True
            _checks = [(a.worth, a.suit) for a in pair_1]
            new_cards = [x for x in deepcopy(local_cards) if (x.worth, x.suit) not in _checks]
            pair_2 = self.check_for_worth_matches(new_cards)
            if pair_2:
                self.found = True
                self.high_value = pair_1 + pair_2

        return self.found

    # @property
    # def outs(self):
    #     return 2


class ThreeOfAKind(Pair):
    def __init__(self):
        super(ThreeOfAKind, self).__init__()
        self.name = "Three of a Kind"
        self.ranking = 3
        self.num_to_match = 3

    def check_cards(self, cards):
        found = super(ThreeOfAKind, self).check_cards(cards)
        if not found:
            self.num_to_match = 2
            pair = self.check_for_worth_matches(cards)
            if pair:
                self.close = True
                self.high_value = pair

            self.num_to_match = 3

        return self.found

    # @property
    # def outs(self):
    #     return 3 - len(self.high_value)


class Straight(WinningHand):
    def __init__(self):
        super(Straight, self).__init__()
        self.name = "Straight"
        self.ranking = 4
        self.num_matched = 0

    def check_cards(self, cards):
        straight_found = self.check_for_straight(cards)
        if straight_found:
            sorted_cards = self.get_sorted_cards(cards)
            self.high_value = sorted_cards
        # else:
        #     # new function to see how close we are to a straight
        #     pass

        return straight_found

    def check_for_straight(self, cards):
        """
            Utility function used to check if a straight exists.
        :param list[Card] cards: Cards to check for a straight
        :return: boolean indicating if a straight was found
        :rtype: bool
        """
        sorted_cards = self.get_sorted_cards(cards)
        _prev_val = None
        _interval = 1
        straight_found = True
        for _c in sorted_cards:
            if _prev_val is None:
                _prev_val = _c.worth
                continue

            if _c.worth != _prev_val - _interval:
                straight_found = False
                break

            _prev_val = _c.worth

        return straight_found


class Flush(WinningHand):
    def __init__(self):
        super(Flush, self).__init__()
        self.name = "Flush"
        self.ranking = 5
        self.num_matched = 0

    def check_cards(self, cards):
        self.found = self.check_for_flush(cards)

        if self.found:
            self.high_value = self.get_sorted_cards(cards)

        return self.found

    def check_for_flush(self, cards):
        """
            Utility function used to check if a flush exists.
        :param list[Card] cards: Cards to check for a flush
        :return: boolean indicating if a flush was found
        :rtype: bool
        """
        flush_found = False
        card_suits = [x.suit for x in cards]
        if len(set(card_suits)) == 1:
            flush_found = True
        # else:
        #     suit_map = {}
        #     for _c in cards:
        #         if _c.suit not in suit_map.keys():
        #             suit_map[_c.suit] = []
        #         suit_map[_c.suit].append(_c)
        #     four_card_suits = [suit for suit, cards in suit_map.items() if len(cards) == 4]
        #     if four_card_suits:
        #         self.close = True
        #         self.num_matched = 4
        #         self.high_value = suit_map[four_card_suits[0]]
        #     three_card_suits = [suit for suit, matches in suit_map.items() if len(matches) == 3]
        #     if three_card_suits:
        #         self.close = True
        #         self.num_matched = 3
        #         self.high_value = suit_map[three_card_suits[0]]

        return flush_found

    @property
    def outs(self):
        return 5 - len(self.high_value)


class FullHouse(Pair):
    def __init__(self):
        super(FullHouse, self).__init__()
        self.name = "Full House"
        self.ranking = 6

    def check_cards(self, cards):
        local_cards = deepcopy(cards)
        self.num_to_match = 3
        three_found = self.check_for_worth_matches(local_cards)
        if three_found:
            _checks = [(a.worth, a.suit) for a in three_found]
            new_cards = [x for x in deepcopy(cards) if (x.worth, x.suit) not in _checks]
            self.num_to_match = 2
            pair = self.check_for_worth_matches(new_cards)
            if pair:
                self.found = True
                self.high_value = pair + three_found

        return self.found


class FourOfAKind(Pair):
    def __init__(self):
        super(FourOfAKind, self).__init__()
        self.name = "Four of a Kind"
        self.ranking = 7
        self.num_to_match = 4


class StraightFlush(Flush, Straight):
    def __init__(self):
        super(StraightFlush, self).__init__()
        self.name = "Straight Flush"
        self.ranking = 8
        self.is_royal = False

    def check_cards(self, cards):
        straight_flush_found = False
        straight_cards = []
        flush_cards = []

        flush_found = self.check_for_flush(cards)
        # if self.close:
        #     flush_cards = deepcopy(self.high_value)

        straight_found = self.check_for_straight(cards)
        # if self.close:
        #     straight_cards = deepcopy(self.high_value)

        if straight_found and flush_found:
            straight_flush_found = True
            self.high_value = self.get_sorted_cards(cards)
            if self.high_value[0].worth == 14:
                self.is_royal = True
                self.ranking += 1
                self.name = "Royal Flush"

        # else:
        #     if straight_cards and flush_cards:
        #         self.close = True
        #         self.high_value = [x for x in straight_cards if x in flush_cards]

        return straight_flush_found

    # @property
    # def outs(self):
    #     return 5 - len(self.high_value)


# In order so once we can check if it's the best hand more efficiently
WINNING_HANDS = (
    StraightFlush,
    FourOfAKind,
    FullHouse,
    Flush,
    Straight,
    ThreeOfAKind,
    TwoPair,
    Pair,
    HighCard,
)


class Card(object):
    """ Class to represent an individual playing card. """
    def __init__(self, worth, suit):
        """
            Create an individual playing card.
        :param int worth: The value of the card.
        :param str suit: The suit of the card.
        """
        self.worth = worth
        self.suit = suit

    def __str__(self):
        """ Update string representation method of class to return the card's identity in a 'pretty' format. """
        if self.worth > 10:
            if self.worth == 11:
                _worth = "Jack"
            elif self.worth == 12:
                _worth = "Queen"
            elif self.worth == 13:
                _worth = "King"
            else:
                _worth = "Ace"
        else:
            _worth = self.worth
        return f"{_worth} of {self.suit}"


class Deck(object):
    """ Class to represent a full deck of playing cards. """
    def __init__(self):
        self.max_num_cards = 52
        self.available_cards = []
        self.dealt_cards = []
        self.community_cards = []
        self.burnt_cards = []

        # Create the actual card instances
        for _s in SUITS:
            for _w in WORTHS:
                self.available_cards.append(Card(worth=_w, suit=_s))

        # Shuffle the cards a random number of times
        for _ in range(secrets.randbelow(7)):
            random.shuffle(self.available_cards)

    def _deal_card(self):
        """
            Choose a card at random from the available cards in the deck and return it, removing it from the available
            cards in the deck.
        :return: The card chosen at random.
        :rtype: Card
        """
        card = secrets.choice(self.available_cards)
        self.available_cards.remove(card)
        return card

    def _find_card(self, worth, suit):
        """
            Get a specific card from the deck, if it exists.
        :param int worth: Card's worth
        :param str suit: Card's suit
        :return: Card, if it was found, or None if not
        :rtype: Card
        """
        _card = None
        for _c in self.available_cards:
            if _c.suit[0].lower() == suit and _c.worth == worth:
                _card = _c
                break
        self.available_cards.remove(_card)
        return _card

    @property
    def num_cards_available(self):
        """
            Get the number of available cards in the deck.  Can be useful for calculating odds.
        :return: integer representing the number of cards remaining in the deck.
        :rtype: int
        """
        return len(self.available_cards)

    def get_player_card(self, card_str):
        """
            Find the Card based on the given card_str param and return it.
        :param str card_str: string in the format of '<worth><suit>' where suit is 1 string character and worth is an int
        :return: Card described in the card_str
        :rtype: Card
        """
        suit = card_str[-1]
        worth = int(card_str[:-1])
        return self._find_card(worth=worth, suit=suit)

    def set_community_card(self, card_str):
        """
            Set a community card based on a given card_str
        :param str card_str: string in the format of '<worth><suit>' where suit is 1 string character and worth is an int
        :return: N/A
        """
        suit = card_str[-1]
        worth = int(card_str[:-1])
        self.community_cards.append(self._find_card(worth=worth, suit=suit))

    def deal_to_players(self, players, num_cards=2):
        """
            Deal to each of the provided players the specified number of cards.
        :param list[Player] players: list of Players to be dealt cards.
        :param int num_cards: number of cards to be dealt to each Player; default is 2
        :return: N/A
        """
        for i in range(num_cards):
            for _player in players:
                _card = self._deal_card()
                _player.add_card(_card)
                self.dealt_cards.append(_card)

    def deal_flop(self):
        """
            Deal The Flop:  Burns one card and adds 3 cards to the community cards.
        :return: N/A
        """
        self._burn_card()

        for i in range(3):
            _card = self._deal_card()
            self.community_cards.append(_card)

    def deal_river(self):
        """
            Deal The River: Burns one card and adds 1 card to the community cards.
        :return: N/A
        """
        self._burn_card()

        _card = self._deal_card()
        self.community_cards.append(_card)

    def deal_turn(self):
        """
            Deal The Turn.  Burns one card and adds 1 card to the community cards.
        :return: N/A
        """
        self._burn_card()

        _card = self._deal_card()
        self.community_cards.append(_card)

    def _burn_card(self):
        """
            Dealer removes a card from play.  This is known as 'burning' a card.
        :return: N/A
        """
        self.burnt_cards.append(self._deal_card())


class Player(object):

    def __init__(self, player_num, possible_hands):
        self.player_id = player_num
        self.cards = []
        self.best_hand = None
        self.odds = {}

        self._completed_hands = []
        self._possible_hands = possible_hands

    def add_card(self, card):
        """
            Adds a dealt Card to the Player's cards
        :param card:
        :return:
        """
        self.cards.append(card)

    def get_card_combos(self, community_cards, num_cards=5):
        """
            Create a list of possible combinations of the community Cards, with num_cards
            specifying how many cards are in each combination.  This number is subtracted from the number of Player
            cards to use that number of Cards in each combination.
        :param list[Card] community_cards: The community cards available to the Player
        :param int num_cards: number of total cards in the hand; default is 5
        :return: list of lists containing all possible card combinations
        :rtype: list[list[Card]]
        """
        available_community_spots = num_cards - len(self.cards)
        _community = deepcopy(community_cards)
        combos_raw = combinations(_community, available_community_spots)
        combos = [list(x) for x in combos_raw]
        return combos

    def check_cards_for_winning_hands(self, community_cards):
        """
            Check the given community cards against the Player's own cards to see if there are any winning hands or any
            better winning hands if one was found previously.
        :param list[Card] community_cards: list of community Cards available to the player
        :return: N/A
        """
        # Stats vars
        unseen = TOTAL_CARDS_IN_DECK - len(community_cards)
        remaining_community = 5 - len(community_cards)

        player_cards = deepcopy(self.cards)
        community_combos = self.get_card_combos(community_cards)

        for _combo in community_combos:
            player_hand = _combo + player_cards
            winning_hands = [x() for x in self._possible_hands]

            for _hand in winning_hands:
                completed = _hand.check_cards(player_hand)
                if completed:
                    self._completed_hands.append(_hand)
                    if self.best_hand is None:
                        self.best_hand = _hand
                        break
                    else:
                        if self.best_hand.ranking < _hand.ranking:
                            self.best_hand = _hand
                            break
                        elif self.best_hand.ranking == _hand.ranking:
                            current_highest = self.best_hand.high_value[0].worth
                            new_highest = _hand.high_value[0].worth
                            if new_highest > current_highest:
                                self.best_hand = _hand
                                break
                # else:
                #     if _hand.close:
                #         self._possible_hands.append(_hand)
                #         _hand.calculate_odds(num_unseen_cards=unseen,
                #                              remaining_community_cards=remaining_community)


class TexasHoldEm(object):
    def __init__(self, num_cards_per_player=2, num_players=6, winning_hands=WINNING_HANDS):

        self.num_cards_per_player = num_cards_per_player
        self.deck = Deck()
        self.winning_hands = deepcopy(winning_hands)

        # Need to define starting player:
        self.deal_players = self._make_players(num_players=num_players - 1)
        self.user_player = self.user_player = Player(player_num=num_players-1, possible_hands=self.winning_hands)
        self.players = [*self.deal_players, self.user_player]
        self.dealer = self.players[0].player_id

    def run_monte_carlo(self, player_cards, community_cards=None, num_games=10000):
        """
            Run a Monte Carlo simulation to determine the statistics of the User's chances of winning given the User's
            input cards and any Community cards, if they exist.  Return a string to print with the User's statistics
            synopsis for this the simulation.
        :param list[str] player_cards: list of card_str representing the User's cards
        :param list[str] or None community_cards: list of card_str representing the existing Community Cards, if they exist
        :param int num_games: Number of games to run in the simulation; default of 10,000.
        :return: string containing a percentage of games the user one and the top hands from all of the wins.
        :rtype: str
        """
        player_wins = {}
        for __ in range(num_games):
            if community_cards is not None:
                for _ccs in deepcopy(community_cards):
                    self.deck.set_community_card(_ccs)

            for _cs in deepcopy(player_cards):
                self.user_player.add_card(self.deck.get_player_card(_cs))

            winning_player, winning_hand = self._play_hand()

            if winning_player == self.user_player.player_id:
                if winning_hand not in player_wins.keys():
                    player_wins[winning_hand] = 0
                player_wins[winning_hand] += 1

            self._end_hand()

        # Calculate stats
        total_player_wins = sum(player_wins.values())
        player_win_average = total_player_wins / num_games
        sorted_win_counts = sorted(list(player_wins.values()))
        win_range = 3 if len(sorted_win_counts) >= 3 else len(sorted_win_counts)
        wins = []
        if sorted_win_counts:
            for i in range(win_range):
                wins.append(list(player_wins.keys())[list(player_wins.values()).index(sorted_win_counts[i])])

        _win_str = '\n\t'.join(wins)
        _msg = f"Player wins {player_win_average * 100:.2f}% of the time.  Most victories are won by: \n\t{_win_str}"
        return _msg

    @property
    def community_cards(self):
        """
            QoL function to quickly return the game's Community cards.
        :return: the list of Cards that the community has access too
        :rtype: list[Card]
        """
        return self.deck.community_cards

    def _make_players(self, num_players):
        """
            Utility function to quickly create new players given an input number of players.
        :param int num_players: the number of players to create.
        :return: list of created Players
        :rtype: list[Player]
        """
        return [Player(player_num=x, possible_hands=self.winning_hands) for x in range(num_players)]

    def _play_hand(self):
        """
            QoL function to represent playing a full hand of Texas Hold 'Em poker.
        :return: Winner's player ID and the winning hand's name
        :rtype: (int,str)
        """
        self.deck.deal_to_players(self.deal_players)
        if len(self.community_cards) == 0:
            self.deck.deal_flop()
            # leader = self._check_player_hands()
        if len(self.community_cards) == 3:
            self.deck.deal_turn()
            # leader = self._check_player_hands()
        if len(self.community_cards) == 4:
            self.deck.deal_river()
        leader = self._check_player_hands()

        return leader.player_id, leader.best_hand.name

    def _end_hand(self):
        """
            QoL function to reset/clean up after each hand and get ready to play the next round of the simulation.
            Clear the players cards and winning hands then create and shuffle a new deck.

            Later we can add moving players through the list of players to be dealt appropriately to try and increase simulation realism.
        :return: N/A
        """
        # Clear players hands
        for player in self.players:
            player.best_hand = None
            player.cards = []
            player._completed_hands = []

        # Get next dealer
        if self.dealer + 1 > len(self.players):
            self.dealer = self.players[0].player_id
        else:
            self.dealer += 1
        # TODO: remake list from new dealer perspective

        # Fresh deck and will be shuffled and have all cards in it
        self.deck = Deck()

    def _check_player_hands(self):
        """
            Utility function to have each Player check their own hands, then see if they have the best hand.
        :return: Player with the best hand
        :rtype: Player
        """
        current_leader = None
        for _player in self.players:
            _player.check_cards_for_winning_hands(self.community_cards)
            if _player.best_hand is not None:
                if current_leader is None:
                    current_leader = _player
                else:
                    if _player.best_hand.ranking > current_leader.best_hand.ranking:
                        current_leader = _player
                    elif _player.best_hand.ranking == current_leader.best_hand.ranking:
                        current_highest = current_leader.best_hand.high_value[0].worth
                        new_highest = _player.best_hand.high_value[0].worth
                        if new_highest > current_highest:
                            current_leader = _player
        return current_leader


def test_monte_carlo():
    """
        Runs a series of tests to ensure the classes and functions are working appropriately.
    :return: N/A
    """
    print("MONTE CARLO TEST: BEGIN")

    # Confirm that HighCard is found when running the simulation
    print("High Card Test: Running...")
    holdem_hc = TexasHoldEm(num_players=2, winning_hands=(HighCard, ))
    hc_msg = holdem_hc.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '2s', '3s', '2h'],
        num_games=10
    )
    print(f"High Card Test: {hc_msg}")
    if "High Card" not in hc_msg:
        print("High Card Test: Failed.  Hand Type missing.")
    else:
        print("High Card Test: Passed.")

    # Confirm that a Pair is found
    print("Pair Test: Running...")
    holdem_p = TexasHoldEm(num_players=2, winning_hands=(Pair, HighCard))
    p_msg = holdem_p.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '4s', '5s', '14h'],
        num_games=10
    )
    print(f"Pair Test: {p_msg}")
    if "Pair" not in p_msg:
        print("Pair Test: Failed.  Hand Type missing.")
    else:
        print("Pair Test: Passed.")

    # Confirm that TwoPair is found
    print("Two Pair Test: Running...")
    holdem_tp = TexasHoldEm(num_players=2, winning_hands=(TwoPair,))
    tp_msg = holdem_tp.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '2s', '3s', '2h'],
        num_games=10
    )
    print(f"Two Pair Test: {tp_msg}")
    if "Two Pair" not in tp_msg:
        print("Two Pair Test: Failed.  Hand Type missing.")
    else:
        print("Two Pair Test: Passed.")

    # Confirm that Three of a Kind is found
    print("Three of a Kind Test: Running...")
    holdem_tk = TexasHoldEm(num_players=2, winning_hands=(ThreeOfAKind,))
    tk_msg = holdem_tk.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '2s', '14d', '14h'],
        num_games=10
    )
    print(f"Three of a Kind Test: {tk_msg}")
    if "Three of a Kind" not in tk_msg:
        print("Three of a Kind Test: Failed.  Hand Type missing.")
    else:
        print("Three of a Kind Test: Passed.")

    # Confirm that a Straight is found
    print("Straight Test: Running...")
    holdem_s = TexasHoldEm(num_players=2, winning_hands=(Straight,))
    s_msg = holdem_s.run_monte_carlo(
        player_cards=['14s', '13c'],
        community_cards=['12c', '11c', '10s', '3s', '2h'],
        num_games=10
    )
    print(f"Straight Test: {s_msg}")
    if "Straight" not in s_msg:
        print("Straight Test: Failed.  Hand Type missing.")
    else:
        print("Straight Test: Passed.")

    # Confirm that a Flush is found
    print("Flush Test: Running...")
    holdem_f = TexasHoldEm(num_players=2, winning_hands=(Flush,))
    f_msg = holdem_f.run_monte_carlo(
        player_cards=['14s', '13s'],
        community_cards=['2s', '3s', '2h', '9s', '3h'],
        num_games=10
    )
    print(f"Flush Test: {f_msg}")
    if "Flush" not in f_msg:
        print("Flush Test: Failed.  Hand Type missing.")
    else:
        print("Flush Test: Passed.")

    # Confirm that Full House is found
    print("Full House Test: Running...")
    holdem_fh = TexasHoldEm(num_players=2, winning_hands=(FullHouse,))
    fh_msg = holdem_fh.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '2s', '3s', '2h'],
        num_games=100
    )
    print(f"Full House Test: {fh_msg}")
    if "Full House" not in fh_msg:
        print("Full House Test: Failed.  Hand Type missing.")
    else:
        print("Full House Test: Passed.")

    # Confirm that FourOfAKind is found
    print("Four of a Kind Test: Running...")
    holdem_fk = TexasHoldEm(num_players=2, winning_hands=(FourOfAKind,))
    fk_msg = holdem_fk.run_monte_carlo(
        player_cards=['14s', '14c'],
        community_cards=['2c', '3c', '2s', '14d', '14h'],
        num_games=1000
    )
    print(f"Four of a Kind Test: {fk_msg}")
    if "Four of a Kind" not in fk_msg:
        print("Four of a Kind Test: Failed.  Hand Type missing.")
    elif "100.00%" not in fk_msg:
        print("Four of a Kind Test: Failed.  Incorrect calculations somewhere.")
    else:
        print("Four of a Kind Test: Passed.")

    # Confirm that StraightFlush is found
    print("Straight Flush Test: Running...")
    holdem_sf = TexasHoldEm(num_players=2, winning_hands=(StraightFlush,))
    sf_msg = holdem_sf.run_monte_carlo(
        player_cards=['13s', '12s'],
        community_cards=['11s', '10s', '9s', '14c', '14h'],
        num_games=1000
    )
    print(f"Straight Flush Test: {sf_msg}")
    if "Straight Flush" not in sf_msg:
        print("Straight Flush Test: Failed.  Hand Type missing.")
    elif "100.00%" not in fk_msg:
        print("Straight Flush Test: Failed.  Incorrect calculations somewhere.")
    else:
        print("Straight Flush Test: Passed.")

    # Confirm that when a Royal Flush is guaranteed the correct words appear in the returned message.
    print("Royal Flush Test: Running...")
    holdem_rf = TexasHoldEm(num_players=2)
    rf_msg = holdem_rf.run_monte_carlo(
        player_cards=['14s', '13s'],
        community_cards=['12s', '11s', '10s', ],
        num_games=1000
    )
    print(f"Royal Flush Test: {rf_msg}")
    if "100.00%" not in rf_msg:
        print("Royal Flush Test:  Failed. Incorrect calculations somewhere.")
    elif "Royal Flush" not in rf_msg:
        print("Royal Flush Test:  Failed. Hand Type missing.")
    else:
        print("Royal Flush Test:  Passed")

    print("MONTE CARLO TEST: FINISHED")


def sanitize_card_string_input(card_string_input):
    """
        Utility function to sanitize the User input from the human-readable format to the format the Deck class expects.
    :param str card_string_input:
    :return: reformatted card_str
    :rtype: str
    """
    card_string = deepcopy(card_string_input.lower())
    if 'j' in card_string:
        card_string.replace('j', '11')
    elif 'q' in card_string:
        card_string.replace('q', '12')
    elif 'k' in card_string:
        card_string.replace('k', '13')
    elif 'a' in card_string:
        card_string.replace('a', '14')

    return card_string


if __name__ == '__main__':
    print("welcome to poker")
    num_players_input = int(input("How many players, including yourself, are in the game? "))
    if num_players_input == 99:
        # Run the test
        test_monte_carlo()
        exit(0)

    if num_players_input > 8:
        print("Sorry but we only support up to 8 players right now.  Please choose again.")
        exit(0)

    try:
        while True:
            print(
                "We need to know the cards you were dealt.  Please enter them in the format of <Card><Suit> with both being 1 character each.  So if you were dealt the 7 of Clubs and the Jack of Spades, those would be '7c' and 'Js' respectively.  ")

            card_1 = sanitize_card_string_input(input("Please enter your first card: "))
            card_2 = sanitize_card_string_input(input("Please enter your second card: "))
            _player_cards = [card_1.lower(), card_2.lower()]

            print("If there are any community cards please enter them one by one; enter 'N' if done or None")
            comm_cards = []
            while True:
                comm_card = input("Any Community Cards? Enter 'N' if done.")
                if comm_card.lower() == 'n':
                    break

                comm_cards.append(sanitize_card_string_input(comm_card))

            hold_em = TexasHoldEm(num_players=num_players_input)
            _community_cards = deepcopy(comm_cards) if comm_cards else None
            msg = hold_em.run_monte_carlo(player_cards=deepcopy(_player_cards), community_cards=_community_cards)
            print(msg)

            play_again = input("Would you like to play again? (Y/N) ")
            # Ask to play again
            if play_again.lower() != 'Y':
                raise EndGame("blah blah")

    except EndGame:
        print("Thanks for stopping by! Goodbye")
        exit(0)
    except KeyboardInterrupt:
        print("Hard Exit")
        exit(0)
    except Exception as e:
        print(f"Got a bad thing: {e}")
        exit(1)
